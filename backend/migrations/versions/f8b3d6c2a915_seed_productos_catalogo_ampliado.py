"""seed: 10 productos nuevos del catalogo ampliado (Camisas/Chalecos/etc.)

Estos 10 productos se cargaron directo en la base de produccion (Supabase)
via REST, sin pasar por una migracion -- por eso no aparecian en el
historial de Alembic y cualquiera que clonara el repo de nuevo (una
companera de equipo, por ejemplo) no los iba a tener en su Postgres local
al correr `alembic upgrade head`. Esta migracion los recrea, con los MISMOS
ids que ya tienen en produccion, para que el catalogo local quede
identico. No incluye imagenes, inventario ni la plantilla del probador AR
(eso se carga aparte, por sucursal/foto real, no tiene sentido clonarlo).

Revision ID: f8b3d6c2a915
Revises: e4a7c1f9b356
Create Date: 2026-09-18

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f8b3d6c2a915"
down_revision = "e4a7c1f9b356"
branch_labels = None
depends_on = None

PRODUCTOS = [
    (13, 1, 11, 107, 1, 1, "Camisa Cuadros Flanela", "Camisa de flanela a cuadros.", "180.00"),
    (14, 1, 12, 108, 2, 2, "Camisa Blanca Oxford", "Camisa oxford clasica de algodon.", "165.00"),
    (15, 2, 3, 101, 1, 1, "Pantalon Cargo Verde", "Pantalon cargo con bolsillos laterales.", "195.00"),
    (16, 3, 4, 105, 1, 1, "Chaqueta Bomber Verde Militar", "Chaqueta bomber con forro interno.", "380.00"),
    (17, 5, 5, 106, 2, 2, "Gorra Trucker Blanca", "Gorra trucker con malla trasera.", "85.00"),
    (18, 7, 3, 110, 2, 2, "Polera Rayas Marino", "Polera a rayas de algodon.", "140.00"),
    (19, 7, 8, 108, 2, 2, "Polera Estampada Retro", "Polera con estampado retro.", "175.00"),
    (20, 8, 5, 104, 1, 1, "Chaleco Acolchado Negro", "Chaleco acolchado sin mangas.", "210.00"),
    (21, 9, 4, 109, 1, 1, "Hoodie Negra Capucha", "Hoodie con capucha y bolsillo canguro.", "230.00"),
    (22, 10, 1, 107, 1, 1, "Chompa Cuello V Gris", "Chompa tejida cuello en V.", "195.00"),
]

INSERT_SQL = """
INSERT INTO producto (id, categoria_id, marca_id, proveedor_id, temporada_id, coleccion_id, nombre, descripcion, precio, estado)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'activo')
ON CONFLICT (id) DO NOTHING;
"""

# INSERT con id explicito no mueve la secuencia del SERIAL -- sin esto, el
# proximo producto creado desde el panel admin (que si usa nextval()) podria
# pisar uno de estos ids.
BUMP_SEQUENCE_SQL = """
SELECT setval('producto_id_seq', (SELECT MAX(id) FROM producto));
"""


def upgrade() -> None:
    conn = op.get_bind()
    for p in PRODUCTOS:
        conn.exec_driver_sql(INSERT_SQL, p)
    conn.exec_driver_sql(BUMP_SEQUENCE_SQL)


def downgrade() -> None:
    conn = op.get_bind()
    ids = tuple(p[0] for p in PRODUCTOS)
    conn.exec_driver_sql("DELETE FROM producto WHERE id IN %s;", (ids,))
