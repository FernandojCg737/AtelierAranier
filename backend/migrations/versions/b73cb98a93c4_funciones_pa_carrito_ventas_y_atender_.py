"""funciones/PA: carrito, ventas y atender reserva (CU11)

Revision ID: b73cb98a93c4
Revises: d42180b55571
Create Date: 2026-09-13

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b73cb98a93c4"
down_revision = "d42180b55571"
branch_labels = None
depends_on = None


# item_linea/venta usan herencia por tabla unida (una fila en la tabla base +
# una fila en la tabla de la subclase, ligadas por el mismo id). Las FK que
# hoy tienen las subclases hacia la tabla base no tenian ON DELETE CASCADE
# (SQLAlchemy no lo agrega solo) -- se agrega aca para que las funciones de
# abajo puedan borrar en cascada en vez de tener que hacerlo fila por fila
# a mano en cada procedimiento.
CASCADE_FKS = """
ALTER TABLE detalle_carrito DROP CONSTRAINT detalle_carrito_id_fkey;
ALTER TABLE detalle_carrito ADD CONSTRAINT detalle_carrito_id_fkey
    FOREIGN KEY (id) REFERENCES item_linea(id) ON DELETE CASCADE;

ALTER TABLE detalle_reserva DROP CONSTRAINT detalle_reserva_id_fkey;
ALTER TABLE detalle_reserva ADD CONSTRAINT detalle_reserva_id_fkey
    FOREIGN KEY (id) REFERENCES item_linea(id) ON DELETE CASCADE;

ALTER TABLE detalle_venta_presencial DROP CONSTRAINT detalle_venta_presencial_id_fkey;
ALTER TABLE detalle_venta_presencial ADD CONSTRAINT detalle_venta_presencial_id_fkey
    FOREIGN KEY (id) REFERENCES item_linea(id) ON DELETE CASCADE;

ALTER TABLE detalle_venta_digital DROP CONSTRAINT detalle_venta_digital_id_fkey;
ALTER TABLE detalle_venta_digital ADD CONSTRAINT detalle_venta_digital_id_fkey
    FOREIGN KEY (id) REFERENCES item_linea(id) ON DELETE CASCADE;

ALTER TABLE venta_presencial DROP CONSTRAINT venta_presencial_id_fkey;
ALTER TABLE venta_presencial ADD CONSTRAINT venta_presencial_id_fkey
    FOREIGN KEY (id) REFERENCES venta(id) ON DELETE CASCADE;

ALTER TABLE venta_digital DROP CONSTRAINT venta_digital_id_fkey;
ALTER TABLE venta_digital ADD CONSTRAINT venta_digital_id_fkey
    FOREIGN KEY (id) REFERENCES venta(id) ON DELETE CASCADE;

ALTER TABLE pago DROP CONSTRAINT pago_venta_id_fkey;
ALTER TABLE pago ADD CONSTRAINT pago_venta_id_fkey
    FOREIGN KEY (venta_id) REFERENCES venta(id) ON DELETE CASCADE;

ALTER TABLE transaccion DROP CONSTRAINT transaccion_pago_id_fkey;
ALTER TABLE transaccion ADD CONSTRAINT transaccion_pago_id_fkey
    FOREIGN KEY (pago_id) REFERENCES pago(id) ON DELETE CASCADE;
"""

# ---------------------------------------------------------------- carrito --

SP_OBTENER_O_CREAR_CARRITO = """
CREATE OR REPLACE FUNCTION sp_obtener_o_crear_carrito(p_cliente_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_carrito_id INTEGER;
BEGIN
    SELECT id INTO v_carrito_id FROM carrito WHERE cliente_id = p_cliente_id AND estado = 'activo';
    IF v_carrito_id IS NULL THEN
        INSERT INTO carrito (cliente_id, fecha_creacion, estado)
        VALUES (p_cliente_id, now(), 'activo')
        RETURNING id INTO v_carrito_id;
    END IF;
    RETURN v_carrito_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_AGREGAR_ITEM_CARRITO = """
CREATE OR REPLACE FUNCTION sp_agregar_item_carrito(
    p_carrito_id INTEGER, p_producto_id INTEGER, p_talla_id INTEGER, p_color_id INTEGER,
    p_cantidad INTEGER, p_precio_unitario NUMERIC(10,2)
) RETURNS INTEGER AS $$
DECLARE
    v_detalle_id INTEGER;
BEGIN
    IF p_cantidad < 1 THEN
        RAISE EXCEPTION 'cantidad_invalida';
    END IF;

    SELECT dc.id INTO v_detalle_id
    FROM detalle_carrito dc
    JOIN item_linea il ON il.id = dc.id
    WHERE dc.carrito_id = p_carrito_id AND il.producto_id = p_producto_id
      AND il.talla_id = p_talla_id AND il.color_id = p_color_id;

    IF v_detalle_id IS NOT NULL THEN
        UPDATE item_linea SET cantidad = cantidad + p_cantidad WHERE id = v_detalle_id;
        UPDATE detalle_carrito SET precio_unitario = p_precio_unitario WHERE id = v_detalle_id;
    ELSE
        INSERT INTO item_linea (producto_id, talla_id, color_id, cantidad, tipo)
        VALUES (p_producto_id, p_talla_id, p_color_id, p_cantidad, 'detalle_carrito')
        RETURNING id INTO v_detalle_id;

        INSERT INTO detalle_carrito (id, carrito_id, precio_unitario)
        VALUES (v_detalle_id, p_carrito_id, p_precio_unitario);
    END IF;

    RETURN v_detalle_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_ACTUALIZAR_ITEM_CARRITO = """
CREATE OR REPLACE FUNCTION sp_actualizar_item_carrito(p_detalle_id INTEGER, p_cantidad INTEGER)
RETURNS VOID AS $$
BEGIN
    IF p_cantidad < 1 THEN
        RAISE EXCEPTION 'cantidad_invalida';
    END IF;
    UPDATE item_linea SET cantidad = p_cantidad WHERE id = p_detalle_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'item_no_encontrado';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

SP_ELIMINAR_ITEM_CARRITO = """
CREATE OR REPLACE FUNCTION sp_eliminar_item_carrito(p_detalle_id INTEGER)
RETURNS VOID AS $$
BEGIN
    DELETE FROM item_linea WHERE id = p_detalle_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_VACIAR_CARRITO = """
CREATE OR REPLACE FUNCTION sp_vaciar_carrito(p_carrito_id INTEGER)
RETURNS VOID AS $$
BEGIN
    DELETE FROM item_linea WHERE id IN (SELECT id FROM detalle_carrito WHERE carrito_id = p_carrito_id);
END;
$$ LANGUAGE plpgsql;
"""

# ----------------------------------------------------------------- ventas --
# p_items es un JSONB tipo [{"producto_id":6,"talla_id":3,"color_id":6,"cantidad":2}, ...]
# -- la validacion "amigable" (nombre del producto en el mensaje de error)
# sigue en Python antes de llamar a la funcion; RAISE EXCEPTION aca es el
# resguardo de bajo nivel ante condiciones de carrera, igual que ya hacen
# sp_establecer_inventario/sp_actualizar_inventario_cantidad.

SP_CREAR_VENTA_PRESENCIAL = """
CREATE OR REPLACE FUNCTION sp_crear_venta_presencial(
    p_cliente_id INTEGER, p_sucursal_id INTEGER, p_empleado_id INTEGER, p_items JSONB
) RETURNS INTEGER AS $$
DECLARE
    v_venta_id INTEGER;
    v_item JSONB;
    v_precio NUMERIC(10,2);
    v_total NUMERIC(10,2) := 0;
    v_inventario_id INTEGER;
    v_stock INTEGER;
    v_detalle_id INTEGER;
BEGIN
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
        SELECT precio INTO v_precio FROM producto WHERE id = (v_item->>'producto_id')::INTEGER;
        IF v_precio IS NULL THEN
            RAISE EXCEPTION 'producto_no_encontrado';
        END IF;

        SELECT id, cantidad INTO v_inventario_id, v_stock FROM inventario
        WHERE producto_id = (v_item->>'producto_id')::INTEGER AND talla_id = (v_item->>'talla_id')::INTEGER
          AND color_id = (v_item->>'color_id')::INTEGER AND sucursal_id = p_sucursal_id
        FOR UPDATE;

        IF v_inventario_id IS NULL OR v_stock < (v_item->>'cantidad')::INTEGER THEN
            RAISE EXCEPTION 'stock_insuficiente';
        END IF;

        v_total := v_total + v_precio * (v_item->>'cantidad')::INTEGER;
    END LOOP;

    INSERT INTO venta (cliente_id, sucursal_id, fecha, total, estado, tipo)
    VALUES (p_cliente_id, p_sucursal_id, now(), v_total, 'pagada', 'venta_presencial')
    RETURNING id INTO v_venta_id;

    INSERT INTO venta_presencial (id, empleado_id) VALUES (v_venta_id, p_empleado_id);

    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
        SELECT precio INTO v_precio FROM producto WHERE id = (v_item->>'producto_id')::INTEGER;

        INSERT INTO item_linea (producto_id, talla_id, color_id, cantidad, tipo)
        VALUES (
            (v_item->>'producto_id')::INTEGER, (v_item->>'talla_id')::INTEGER,
            (v_item->>'color_id')::INTEGER, (v_item->>'cantidad')::INTEGER, 'detalle_venta_presencial'
        )
        RETURNING id INTO v_detalle_id;

        INSERT INTO detalle_venta_presencial (id, venta_presencial_id, precio_unitario)
        VALUES (v_detalle_id, v_venta_id, v_precio);

        UPDATE inventario SET cantidad = cantidad - (v_item->>'cantidad')::INTEGER
        WHERE producto_id = (v_item->>'producto_id')::INTEGER AND talla_id = (v_item->>'talla_id')::INTEGER
          AND color_id = (v_item->>'color_id')::INTEGER AND sucursal_id = p_sucursal_id
        RETURNING id INTO v_inventario_id;

        INSERT INTO movimiento_inventario (inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia)
        VALUES (v_inventario_id, p_empleado_id, 'salida', (v_item->>'cantidad')::INTEGER, now(),
                'Venta presencial #' || v_venta_id);
    END LOOP;

    INSERT INTO pago (venta_id, monto, metodo, estado, fecha)
    VALUES (v_venta_id, v_total, 'efectivo', 'completado', now());

    RETURN v_venta_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_CREAR_VENTA_DIGITAL_PAYPAL = """
CREATE OR REPLACE FUNCTION sp_crear_venta_digital_paypal(
    p_cliente_id INTEGER, p_sucursal_id INTEGER, p_carrito_id INTEGER, p_items JSONB,
    p_referencia_externa VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    v_venta_id INTEGER;
    v_pago_id INTEGER;
    v_item JSONB;
    v_precio NUMERIC(10,2);
    v_total NUMERIC(10,2) := 0;
    v_inventario_id INTEGER;
    v_stock INTEGER;
    v_detalle_id INTEGER;
BEGIN
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
        SELECT precio INTO v_precio FROM producto WHERE id = (v_item->>'producto_id')::INTEGER;
        IF v_precio IS NULL THEN
            RAISE EXCEPTION 'producto_no_encontrado';
        END IF;

        SELECT id, cantidad INTO v_inventario_id, v_stock FROM inventario
        WHERE producto_id = (v_item->>'producto_id')::INTEGER AND talla_id = (v_item->>'talla_id')::INTEGER
          AND color_id = (v_item->>'color_id')::INTEGER AND sucursal_id = p_sucursal_id
        FOR UPDATE;

        IF v_inventario_id IS NULL OR v_stock < (v_item->>'cantidad')::INTEGER THEN
            RAISE EXCEPTION 'stock_insuficiente';
        END IF;

        v_total := v_total + v_precio * (v_item->>'cantidad')::INTEGER;
    END LOOP;

    INSERT INTO venta (cliente_id, sucursal_id, fecha, total, estado, tipo)
    VALUES (p_cliente_id, p_sucursal_id, now(), v_total, 'pagada', 'venta_digital')
    RETURNING id INTO v_venta_id;

    INSERT INTO venta_digital (id, carrito_id) VALUES (v_venta_id, p_carrito_id);

    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
        SELECT precio INTO v_precio FROM producto WHERE id = (v_item->>'producto_id')::INTEGER;

        INSERT INTO item_linea (producto_id, talla_id, color_id, cantidad, tipo)
        VALUES (
            (v_item->>'producto_id')::INTEGER, (v_item->>'talla_id')::INTEGER,
            (v_item->>'color_id')::INTEGER, (v_item->>'cantidad')::INTEGER, 'detalle_venta_digital'
        )
        RETURNING id INTO v_detalle_id;

        INSERT INTO detalle_venta_digital (id, venta_digital_id, precio_unitario)
        VALUES (v_detalle_id, v_venta_id, v_precio);

        UPDATE inventario SET cantidad = cantidad - (v_item->>'cantidad')::INTEGER
        WHERE producto_id = (v_item->>'producto_id')::INTEGER AND talla_id = (v_item->>'talla_id')::INTEGER
          AND color_id = (v_item->>'color_id')::INTEGER AND sucursal_id = p_sucursal_id
        RETURNING id INTO v_inventario_id;

        INSERT INTO movimiento_inventario (inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia)
        VALUES (v_inventario_id, NULL, 'salida', (v_item->>'cantidad')::INTEGER, now(),
                'Venta digital #' || v_venta_id || ' (PayPal ' || p_referencia_externa || ')');
    END LOOP;

    INSERT INTO pago (venta_id, monto, metodo, estado, fecha)
    VALUES (v_venta_id, v_total, 'paypal', 'completado', now())
    RETURNING id INTO v_pago_id;

    INSERT INTO transaccion (pago_id, pasarela, referencia_externa, estado, fecha)
    VALUES (v_pago_id, 'paypal', p_referencia_externa, 'completado', now());

    UPDATE carrito SET estado = 'convertido' WHERE id = p_carrito_id;

    RETURN v_venta_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_CREAR_VENTA_DIGITAL_QR = """
CREATE OR REPLACE FUNCTION sp_crear_venta_digital_qr(
    p_cliente_id INTEGER, p_sucursal_id INTEGER, p_carrito_id INTEGER, p_items JSONB,
    p_comprobante_url VARCHAR
) RETURNS INTEGER AS $$
DECLARE
    v_venta_id INTEGER;
    v_item JSONB;
    v_precio NUMERIC(10,2);
    v_total NUMERIC(10,2) := 0;
    v_detalle_id INTEGER;
BEGIN
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
        SELECT precio INTO v_precio FROM producto WHERE id = (v_item->>'producto_id')::INTEGER;
        IF v_precio IS NULL THEN
            RAISE EXCEPTION 'producto_no_encontrado';
        END IF;
        v_total := v_total + v_precio * (v_item->>'cantidad')::INTEGER;
    END LOOP;

    -- No se descuenta stock todavia: el pago QR queda 'verificando' hasta
    -- que un cajero/encargado lo apruebe (ver sp_aprobar_pago_qr).
    INSERT INTO venta (cliente_id, sucursal_id, fecha, total, estado, tipo)
    VALUES (p_cliente_id, p_sucursal_id, now(), v_total, 'pendiente', 'venta_digital')
    RETURNING id INTO v_venta_id;

    INSERT INTO venta_digital (id, carrito_id) VALUES (v_venta_id, p_carrito_id);

    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
        SELECT precio INTO v_precio FROM producto WHERE id = (v_item->>'producto_id')::INTEGER;

        INSERT INTO item_linea (producto_id, talla_id, color_id, cantidad, tipo)
        VALUES (
            (v_item->>'producto_id')::INTEGER, (v_item->>'talla_id')::INTEGER,
            (v_item->>'color_id')::INTEGER, (v_item->>'cantidad')::INTEGER, 'detalle_venta_digital'
        )
        RETURNING id INTO v_detalle_id;

        INSERT INTO detalle_venta_digital (id, venta_digital_id, precio_unitario)
        VALUES (v_detalle_id, v_venta_id, v_precio);
    END LOOP;

    INSERT INTO pago (venta_id, monto, metodo, estado, fecha, comprobante_url)
    VALUES (v_venta_id, v_total, 'qr', 'verificando', now(), p_comprobante_url);

    UPDATE carrito SET estado = 'convertido' WHERE id = p_carrito_id;

    RETURN v_venta_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_APROBAR_PAGO_QR = """
CREATE OR REPLACE FUNCTION sp_aprobar_pago_qr(p_venta_id INTEGER, p_empleado_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_sucursal_id INTEGER;
    v_pago_id INTEGER;
    v_pago_metodo VARCHAR;
    v_pago_estado VARCHAR;
    v_detalle RECORD;
    v_inventario_id INTEGER;
    v_stock INTEGER;
BEGIN
    SELECT sucursal_id INTO v_sucursal_id FROM venta WHERE id = p_venta_id;
    IF v_sucursal_id IS NULL THEN
        RAISE EXCEPTION 'venta_no_encontrada';
    END IF;

    SELECT id, metodo, estado INTO v_pago_id, v_pago_metodo, v_pago_estado FROM pago WHERE venta_id = p_venta_id;
    IF v_pago_id IS NULL OR v_pago_metodo <> 'qr' OR v_pago_estado <> 'verificando' THEN
        RAISE EXCEPTION 'pago_no_pendiente';
    END IF;

    FOR v_detalle IN
        SELECT il.producto_id, il.talla_id, il.color_id, il.cantidad
        FROM detalle_venta_digital dvd
        JOIN item_linea il ON il.id = dvd.id
        WHERE dvd.venta_digital_id = p_venta_id
    LOOP
        SELECT id, cantidad INTO v_inventario_id, v_stock FROM inventario
        WHERE producto_id = v_detalle.producto_id AND talla_id = v_detalle.talla_id
          AND color_id = v_detalle.color_id AND sucursal_id = v_sucursal_id
        FOR UPDATE;

        IF v_inventario_id IS NULL OR v_stock < v_detalle.cantidad THEN
            RAISE EXCEPTION 'stock_insuficiente';
        END IF;

        UPDATE inventario SET cantidad = cantidad - v_detalle.cantidad WHERE id = v_inventario_id;

        INSERT INTO movimiento_inventario (inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia)
        VALUES (v_inventario_id, p_empleado_id, 'salida', v_detalle.cantidad, now(),
                'Venta digital #' || p_venta_id || ' (QR aprobado)');
    END LOOP;

    UPDATE venta SET estado = 'pagada' WHERE id = p_venta_id;
    UPDATE pago SET estado = 'completado', revisado_por_id = p_empleado_id WHERE id = v_pago_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_RECHAZAR_PAGO_QR = """
CREATE OR REPLACE FUNCTION sp_rechazar_pago_qr(p_venta_id INTEGER, p_empleado_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_pago_id INTEGER;
    v_pago_metodo VARCHAR;
    v_pago_estado VARCHAR;
BEGIN
    SELECT id, metodo, estado INTO v_pago_id, v_pago_metodo, v_pago_estado FROM pago WHERE venta_id = p_venta_id;
    IF v_pago_id IS NULL OR v_pago_metodo <> 'qr' OR v_pago_estado <> 'verificando' THEN
        RAISE EXCEPTION 'pago_no_pendiente';
    END IF;

    UPDATE venta SET estado = 'cancelada' WHERE id = p_venta_id;
    UPDATE pago SET estado = 'rechazado', revisado_por_id = p_empleado_id WHERE id = v_pago_id;
END;
$$ LANGUAGE plpgsql;
"""

SP_EDITAR_VENTA = """
CREATE OR REPLACE FUNCTION sp_editar_venta(
    p_venta_id INTEGER, p_sucursal_id INTEGER, p_items JSONB,
    p_metodo_pago VARCHAR, p_estado_pago VARCHAR, p_empleado_id INTEGER
) RETURNS VOID AS $$
DECLARE
    v_tipo VARCHAR;
    v_estado_anterior VARCHAR;
    v_sucursal_anterior INTEGER;
    v_detalle_tabla VARCHAR;
    v_detalle RECORD;
    v_inventario_id INTEGER;
    v_stock INTEGER;
    v_item JSONB;
    v_precio NUMERIC(10,2);
    v_total NUMERIC(10,2) := 0;
    v_detalle_id INTEGER;
    v_nuevo_estado VARCHAR;
    v_pago_id INTEGER;
BEGIN
    SELECT tipo, estado, sucursal_id INTO v_tipo, v_estado_anterior, v_sucursal_anterior
    FROM venta WHERE id = p_venta_id;
    IF v_tipo IS NULL THEN
        RAISE EXCEPTION 'venta_no_encontrada';
    END IF;
    v_detalle_tabla := CASE WHEN v_tipo = 'venta_presencial' THEN 'detalle_venta_presencial' ELSE 'detalle_venta_digital' END;

    -- 1. si ya estaba pagada, libera el stock viejo (en la sucursal vieja)
    IF v_estado_anterior = 'pagada' THEN
        IF v_tipo = 'venta_presencial' THEN
            FOR v_detalle IN
                SELECT il.producto_id, il.talla_id, il.color_id, il.cantidad
                FROM detalle_venta_presencial d JOIN item_linea il ON il.id = d.id
                WHERE d.venta_presencial_id = p_venta_id
            LOOP
                UPDATE inventario SET cantidad = cantidad + v_detalle.cantidad
                WHERE producto_id = v_detalle.producto_id AND talla_id = v_detalle.talla_id
                  AND color_id = v_detalle.color_id AND sucursal_id = v_sucursal_anterior
                RETURNING id INTO v_inventario_id;
                IF v_inventario_id IS NOT NULL THEN
                    INSERT INTO movimiento_inventario (inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia)
                    VALUES (v_inventario_id, p_empleado_id, 'entrada', v_detalle.cantidad, now(),
                            'Venta #' || p_venta_id || ' editada, stock viejo liberado');
                END IF;
            END LOOP;
        ELSE
            FOR v_detalle IN
                SELECT il.producto_id, il.talla_id, il.color_id, il.cantidad
                FROM detalle_venta_digital d JOIN item_linea il ON il.id = d.id
                WHERE d.venta_digital_id = p_venta_id
            LOOP
                UPDATE inventario SET cantidad = cantidad + v_detalle.cantidad
                WHERE producto_id = v_detalle.producto_id AND talla_id = v_detalle.talla_id
                  AND color_id = v_detalle.color_id AND sucursal_id = v_sucursal_anterior
                RETURNING id INTO v_inventario_id;
                IF v_inventario_id IS NOT NULL THEN
                    INSERT INTO movimiento_inventario (inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia)
                    VALUES (v_inventario_id, p_empleado_id, 'entrada', v_detalle.cantidad, now(),
                            'Venta #' || p_venta_id || ' editada, stock viejo liberado');
                END IF;
            END LOOP;
        END IF;
    END IF;

    -- 2. calcula el total y (si va a quedar pagada) valida/bloquea el stock nuevo
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
        SELECT precio INTO v_precio FROM producto WHERE id = (v_item->>'producto_id')::INTEGER;
        IF v_precio IS NULL THEN
            RAISE EXCEPTION 'producto_no_encontrado';
        END IF;

        IF p_estado_pago = 'completado' THEN
            SELECT id, cantidad INTO v_inventario_id, v_stock FROM inventario
            WHERE producto_id = (v_item->>'producto_id')::INTEGER AND talla_id = (v_item->>'talla_id')::INTEGER
              AND color_id = (v_item->>'color_id')::INTEGER AND sucursal_id = p_sucursal_id
            FOR UPDATE;
            IF v_inventario_id IS NULL OR v_stock < (v_item->>'cantidad')::INTEGER THEN
                RAISE EXCEPTION 'stock_insuficiente';
            END IF;
        END IF;

        v_total := v_total + v_precio * (v_item->>'cantidad')::INTEGER;
    END LOOP;

    -- 3. reemplaza los detalles (borrar el item_linea arrastra la fila de
    -- la subclase por el ON DELETE CASCADE agregado arriba)
    IF v_tipo = 'venta_presencial' THEN
        DELETE FROM item_linea WHERE id IN (SELECT id FROM detalle_venta_presencial WHERE venta_presencial_id = p_venta_id);
    ELSE
        DELETE FROM item_linea WHERE id IN (SELECT id FROM detalle_venta_digital WHERE venta_digital_id = p_venta_id);
    END IF;

    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
        SELECT precio INTO v_precio FROM producto WHERE id = (v_item->>'producto_id')::INTEGER;

        INSERT INTO item_linea (producto_id, talla_id, color_id, cantidad, tipo)
        VALUES (
            (v_item->>'producto_id')::INTEGER, (v_item->>'talla_id')::INTEGER,
            (v_item->>'color_id')::INTEGER, (v_item->>'cantidad')::INTEGER, v_detalle_tabla
        )
        RETURNING id INTO v_detalle_id;

        IF v_tipo = 'venta_presencial' THEN
            INSERT INTO detalle_venta_presencial (id, venta_presencial_id, precio_unitario)
            VALUES (v_detalle_id, p_venta_id, v_precio);
        ELSE
            INSERT INTO detalle_venta_digital (id, venta_digital_id, precio_unitario)
            VALUES (v_detalle_id, p_venta_id, v_precio);
        END IF;

        IF p_estado_pago = 'completado' THEN
            UPDATE inventario SET cantidad = cantidad - (v_item->>'cantidad')::INTEGER
            WHERE producto_id = (v_item->>'producto_id')::INTEGER AND talla_id = (v_item->>'talla_id')::INTEGER
              AND color_id = (v_item->>'color_id')::INTEGER AND sucursal_id = p_sucursal_id
            RETURNING id INTO v_inventario_id;

            INSERT INTO movimiento_inventario (inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia)
            VALUES (v_inventario_id, p_empleado_id, 'salida', (v_item->>'cantidad')::INTEGER, now(),
                    'Venta #' || p_venta_id || ' editada, stock nuevo retenido');
        END IF;
    END LOOP;

    -- 4. actualiza venta y pago
    v_nuevo_estado := CASE p_estado_pago WHEN 'completado' THEN 'pagada' WHEN 'rechazado' THEN 'cancelada' ELSE 'pendiente' END;
    UPDATE venta SET sucursal_id = p_sucursal_id, total = v_total, estado = v_nuevo_estado WHERE id = p_venta_id;

    SELECT id INTO v_pago_id FROM pago WHERE venta_id = p_venta_id;
    IF v_pago_id IS NOT NULL THEN
        UPDATE pago SET
            monto = v_total,
            metodo = p_metodo_pago,
            estado = p_estado_pago,
            revisado_por_id = CASE WHEN p_estado_pago IN ('completado', 'rechazado') THEN p_empleado_id ELSE revisado_por_id END
        WHERE id = v_pago_id;
    ELSE
        INSERT INTO pago (venta_id, monto, metodo, estado, fecha, revisado_por_id)
        VALUES (
            p_venta_id, v_total, p_metodo_pago, p_estado_pago, now(),
            CASE WHEN p_estado_pago IN ('completado', 'rechazado') THEN p_empleado_id ELSE NULL END
        );
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

SP_ELIMINAR_VENTA = """
CREATE OR REPLACE FUNCTION sp_eliminar_venta(p_venta_id INTEGER, p_empleado_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_tipo VARCHAR;
    v_estado VARCHAR;
    v_sucursal_id INTEGER;
    v_detalle RECORD;
    v_inventario_id INTEGER;
BEGIN
    SELECT tipo, estado, sucursal_id INTO v_tipo, v_estado, v_sucursal_id FROM venta WHERE id = p_venta_id;
    IF v_tipo IS NULL THEN
        RAISE EXCEPTION 'venta_no_encontrada';
    END IF;

    IF v_estado = 'pagada' THEN
        IF v_tipo = 'venta_presencial' THEN
            FOR v_detalle IN
                SELECT il.producto_id, il.talla_id, il.color_id, il.cantidad
                FROM detalle_venta_presencial d JOIN item_linea il ON il.id = d.id
                WHERE d.venta_presencial_id = p_venta_id
            LOOP
                UPDATE inventario SET cantidad = cantidad + v_detalle.cantidad
                WHERE producto_id = v_detalle.producto_id AND talla_id = v_detalle.talla_id
                  AND color_id = v_detalle.color_id AND sucursal_id = v_sucursal_id
                RETURNING id INTO v_inventario_id;
                IF v_inventario_id IS NOT NULL THEN
                    INSERT INTO movimiento_inventario (inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia)
                    VALUES (v_inventario_id, p_empleado_id, 'entrada', v_detalle.cantidad, now(),
                            'Venta #' || p_venta_id || ' eliminada, stock devuelto');
                END IF;
            END LOOP;
        ELSE
            FOR v_detalle IN
                SELECT il.producto_id, il.talla_id, il.color_id, il.cantidad
                FROM detalle_venta_digital d JOIN item_linea il ON il.id = d.id
                WHERE d.venta_digital_id = p_venta_id
            LOOP
                UPDATE inventario SET cantidad = cantidad + v_detalle.cantidad
                WHERE producto_id = v_detalle.producto_id AND talla_id = v_detalle.talla_id
                  AND color_id = v_detalle.color_id AND sucursal_id = v_sucursal_id
                RETURNING id INTO v_inventario_id;
                IF v_inventario_id IS NOT NULL THEN
                    INSERT INTO movimiento_inventario (inventario_id, empleado_id, tipo, cantidad, fecha, documento_referencia)
                    VALUES (v_inventario_id, p_empleado_id, 'entrada', v_detalle.cantidad, now(),
                            'Venta #' || p_venta_id || ' eliminada, stock devuelto');
                END IF;
            END LOOP;
        END IF;
    END IF;

    IF v_tipo = 'venta_presencial' THEN
        DELETE FROM item_linea WHERE id IN (SELECT id FROM detalle_venta_presencial WHERE venta_presencial_id = p_venta_id);
    ELSE
        DELETE FROM item_linea WHERE id IN (SELECT id FROM detalle_venta_digital WHERE venta_digital_id = p_venta_id);
    END IF;

    -- ON DELETE CASCADE se lleva venta_presencial/venta_digital, pago y transaccion.
    DELETE FROM venta WHERE id = p_venta_id;
END;
$$ LANGUAGE plpgsql;
"""

# --------------------------------------------------------------- reservas --

SP_ATENDER_RESERVA = """
CREATE OR REPLACE FUNCTION sp_atender_reserva(p_reserva_id INTEGER, p_empleado_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_cliente_id INTEGER;
    v_sucursal_id INTEGER;
    v_estado VARCHAR;
    v_total NUMERIC(10,2) := 0;
    v_venta_id INTEGER;
    v_detalle RECORD;
    v_detalle_id INTEGER;
BEGIN
    SELECT cliente_id, sucursal_id, estado INTO v_cliente_id, v_sucursal_id, v_estado
    FROM reserva WHERE id = p_reserva_id;
    IF v_cliente_id IS NULL THEN
        RAISE EXCEPTION 'reserva_no_encontrada';
    END IF;
    IF v_estado NOT IN ('pendiente', 'confirmada') THEN
        RAISE EXCEPTION 'reserva_no_disponible';
    END IF;

    SELECT COALESCE(SUM(p.precio * il.cantidad), 0) INTO v_total
    FROM detalle_reserva dr JOIN item_linea il ON il.id = dr.id JOIN producto p ON p.id = il.producto_id
    WHERE dr.reserva_id = p_reserva_id;

    -- El stock ya se retuvo al crear la reserva (crear_reserva), asi que
    -- aca no se vuelve a tocar inventario -- solo se deja constancia de la
    -- venta y se cierra la reserva.
    INSERT INTO venta (cliente_id, sucursal_id, fecha, total, estado, tipo)
    VALUES (v_cliente_id, v_sucursal_id, now(), v_total, 'pagada', 'venta_presencial')
    RETURNING id INTO v_venta_id;

    INSERT INTO venta_presencial (id, empleado_id) VALUES (v_venta_id, p_empleado_id);

    FOR v_detalle IN
        SELECT il.producto_id, il.talla_id, il.color_id, il.cantidad, p.precio
        FROM detalle_reserva dr JOIN item_linea il ON il.id = dr.id JOIN producto p ON p.id = il.producto_id
        WHERE dr.reserva_id = p_reserva_id
    LOOP
        INSERT INTO item_linea (producto_id, talla_id, color_id, cantidad, tipo)
        VALUES (v_detalle.producto_id, v_detalle.talla_id, v_detalle.color_id, v_detalle.cantidad, 'detalle_venta_presencial')
        RETURNING id INTO v_detalle_id;

        INSERT INTO detalle_venta_presencial (id, venta_presencial_id, precio_unitario)
        VALUES (v_detalle_id, v_venta_id, v_detalle.precio);
    END LOOP;

    INSERT INTO pago (venta_id, monto, metodo, estado, fecha)
    VALUES (v_venta_id, v_total, 'efectivo', 'completado', now());

    UPDATE reserva SET estado = 'completada' WHERE id = p_reserva_id;

    RETURN v_venta_id;
END;
$$ LANGUAGE plpgsql;
"""

ALL_FUNCTIONS = [
    SP_OBTENER_O_CREAR_CARRITO,
    SP_AGREGAR_ITEM_CARRITO,
    SP_ACTUALIZAR_ITEM_CARRITO,
    SP_ELIMINAR_ITEM_CARRITO,
    SP_VACIAR_CARRITO,
    SP_CREAR_VENTA_PRESENCIAL,
    SP_CREAR_VENTA_DIGITAL_PAYPAL,
    SP_CREAR_VENTA_DIGITAL_QR,
    SP_APROBAR_PAGO_QR,
    SP_RECHAZAR_PAGO_QR,
    SP_EDITAR_VENTA,
    SP_ELIMINAR_VENTA,
    SP_ATENDER_RESERVA,
]

DROP_FUNCTIONS_SQL = """
DROP FUNCTION IF EXISTS sp_obtener_o_crear_carrito(INTEGER);
DROP FUNCTION IF EXISTS sp_agregar_item_carrito(INTEGER, INTEGER, INTEGER, INTEGER, INTEGER, NUMERIC);
DROP FUNCTION IF EXISTS sp_actualizar_item_carrito(INTEGER, INTEGER);
DROP FUNCTION IF EXISTS sp_eliminar_item_carrito(INTEGER);
DROP FUNCTION IF EXISTS sp_vaciar_carrito(INTEGER);
DROP FUNCTION IF EXISTS sp_crear_venta_presencial(INTEGER, INTEGER, INTEGER, JSONB);
DROP FUNCTION IF EXISTS sp_crear_venta_digital_paypal(INTEGER, INTEGER, INTEGER, JSONB, VARCHAR);
DROP FUNCTION IF EXISTS sp_crear_venta_digital_qr(INTEGER, INTEGER, INTEGER, JSONB, VARCHAR);
DROP FUNCTION IF EXISTS sp_aprobar_pago_qr(INTEGER, INTEGER);
DROP FUNCTION IF EXISTS sp_rechazar_pago_qr(INTEGER, INTEGER);
DROP FUNCTION IF EXISTS sp_editar_venta(INTEGER, INTEGER, JSONB, VARCHAR, VARCHAR, INTEGER);
DROP FUNCTION IF EXISTS sp_eliminar_venta(INTEGER, INTEGER);
DROP FUNCTION IF EXISTS sp_atender_reserva(INTEGER, INTEGER);
"""


def upgrade() -> None:
    op.execute(CASCADE_FKS)
    for sql in ALL_FUNCTIONS:
        op.execute(sql)


def downgrade() -> None:
    op.execute(DROP_FUNCTIONS_SQL)
    # Las FK vuelven a quedar sin ON DELETE CASCADE (comportamiento original).
    op.execute("""
        ALTER TABLE detalle_carrito DROP CONSTRAINT detalle_carrito_id_fkey;
        ALTER TABLE detalle_carrito ADD CONSTRAINT detalle_carrito_id_fkey FOREIGN KEY (id) REFERENCES item_linea(id);

        ALTER TABLE detalle_reserva DROP CONSTRAINT detalle_reserva_id_fkey;
        ALTER TABLE detalle_reserva ADD CONSTRAINT detalle_reserva_id_fkey FOREIGN KEY (id) REFERENCES item_linea(id);

        ALTER TABLE detalle_venta_presencial DROP CONSTRAINT detalle_venta_presencial_id_fkey;
        ALTER TABLE detalle_venta_presencial ADD CONSTRAINT detalle_venta_presencial_id_fkey FOREIGN KEY (id) REFERENCES item_linea(id);

        ALTER TABLE detalle_venta_digital DROP CONSTRAINT detalle_venta_digital_id_fkey;
        ALTER TABLE detalle_venta_digital ADD CONSTRAINT detalle_venta_digital_id_fkey FOREIGN KEY (id) REFERENCES item_linea(id);

        ALTER TABLE venta_presencial DROP CONSTRAINT venta_presencial_id_fkey;
        ALTER TABLE venta_presencial ADD CONSTRAINT venta_presencial_id_fkey FOREIGN KEY (id) REFERENCES venta(id);

        ALTER TABLE venta_digital DROP CONSTRAINT venta_digital_id_fkey;
        ALTER TABLE venta_digital ADD CONSTRAINT venta_digital_id_fkey FOREIGN KEY (id) REFERENCES venta(id);

        ALTER TABLE pago DROP CONSTRAINT pago_venta_id_fkey;
        ALTER TABLE pago ADD CONSTRAINT pago_venta_id_fkey FOREIGN KEY (venta_id) REFERENCES venta(id);

        ALTER TABLE transaccion DROP CONSTRAINT transaccion_pago_id_fkey;
        ALTER TABLE transaccion ADD CONSTRAINT transaccion_pago_id_fkey FOREIGN KEY (pago_id) REFERENCES pago(id);
    """)
