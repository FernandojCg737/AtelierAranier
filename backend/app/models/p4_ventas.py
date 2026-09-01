from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ItemLinea(Base):
    __tablename__ = "item_linea"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("producto.id"))
    talla_id: Mapped[int] = mapped_column(ForeignKey("talla.id"))
    color_id: Mapped[int] = mapped_column(ForeignKey("color.id"))
    cantidad: Mapped[int] = mapped_column()
    tipo: Mapped[str] = mapped_column(String(30))

    producto: Mapped["Producto"] = relationship(back_populates="items_linea")
    talla: Mapped["Talla"] = relationship(back_populates="items_linea")
    color: Mapped["Color"] = relationship(back_populates="items_linea")

    __mapper_args__ = {
        "polymorphic_identity": "item_linea",
        "polymorphic_on": "tipo",
    }


class Reserva(Base):
    __tablename__ = "reserva"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"))
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursal.id"))
    horario_atencion: Mapped[datetime] = mapped_column(DateTime)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cliente: Mapped["Cliente"] = relationship(back_populates="reservas")
    sucursal: Mapped["Sucursal"] = relationship(back_populates="reservas")
    detalles: Mapped[list["DetalleReserva"]] = relationship(back_populates="reserva", cascade="all, delete-orphan")


class DetalleReserva(ItemLinea):
    __tablename__ = "detalle_reserva"

    id: Mapped[int] = mapped_column(ForeignKey("item_linea.id"), primary_key=True)
    reserva_id: Mapped[int] = mapped_column(ForeignKey("reserva.id"))

    reserva: Mapped["Reserva"] = relationship(back_populates="detalles")

    __mapper_args__ = {"polymorphic_identity": "detalle_reserva"}


class Carrito(Base):
    __tablename__ = "carrito"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"))
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    estado: Mapped[str] = mapped_column(String(20), default="activo")

    cliente: Mapped["Cliente"] = relationship(back_populates="carritos")
    detalles: Mapped[list["DetalleCarrito"]] = relationship(back_populates="carrito", cascade="all, delete-orphan")
    venta_digital: Mapped["VentaDigital | None"] = relationship(back_populates="carrito")


class DetalleCarrito(ItemLinea):
    __tablename__ = "detalle_carrito"

    id: Mapped[int] = mapped_column(ForeignKey("item_linea.id"), primary_key=True)
    carrito_id: Mapped[int] = mapped_column(ForeignKey("carrito.id"))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    carrito: Mapped["Carrito"] = relationship(back_populates="detalles")

    __mapper_args__ = {"polymorphic_identity": "detalle_carrito"}


class Venta(Base):
    __tablename__ = "venta"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"))
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursal.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    tipo: Mapped[str] = mapped_column(String(30))

    cliente: Mapped["Cliente"] = relationship(back_populates="ventas")
    sucursal: Mapped["Sucursal"] = relationship(back_populates="ventas")
    pago: Mapped["Pago | None"] = relationship(back_populates="venta")

    __mapper_args__ = {
        "polymorphic_identity": "venta",
        "polymorphic_on": "tipo",
    }


class VentaPresencial(Venta):
    __tablename__ = "venta_presencial"

    id: Mapped[int] = mapped_column(ForeignKey("venta.id"), primary_key=True)
    cajero_id: Mapped[int] = mapped_column(ForeignKey("cajero.id"))

    cajero: Mapped["Cajero"] = relationship(back_populates="ventas_atendidas")
    detalles: Mapped[list["DetalleVentaPresencial"]] = relationship(
        back_populates="venta_presencial", cascade="all, delete-orphan"
    )

    __mapper_args__ = {"polymorphic_identity": "venta_presencial"}


class DetalleVentaPresencial(ItemLinea):
    __tablename__ = "detalle_venta_presencial"

    id: Mapped[int] = mapped_column(ForeignKey("item_linea.id"), primary_key=True)
    venta_presencial_id: Mapped[int] = mapped_column(ForeignKey("venta_presencial.id"))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    venta_presencial: Mapped["VentaPresencial"] = relationship(back_populates="detalles")

    __mapper_args__ = {"polymorphic_identity": "detalle_venta_presencial"}


class VentaDigital(Venta):
    __tablename__ = "venta_digital"

    id: Mapped[int] = mapped_column(ForeignKey("venta.id"), primary_key=True)
    carrito_id: Mapped[int] = mapped_column(ForeignKey("carrito.id"), unique=True)

    carrito: Mapped["Carrito"] = relationship(back_populates="venta_digital")
    detalles: Mapped[list["DetalleVentaDigital"]] = relationship(
        back_populates="venta_digital", cascade="all, delete-orphan"
    )

    __mapper_args__ = {"polymorphic_identity": "venta_digital"}


class DetalleVentaDigital(ItemLinea):
    __tablename__ = "detalle_venta_digital"

    id: Mapped[int] = mapped_column(ForeignKey("item_linea.id"), primary_key=True)
    venta_digital_id: Mapped[int] = mapped_column(ForeignKey("venta_digital.id"))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    venta_digital: Mapped["VentaDigital"] = relationship(back_populates="detalles")

    __mapper_args__ = {"polymorphic_identity": "detalle_venta_digital"}


class Pago(Base):
    __tablename__ = "pago"

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("venta.id"), unique=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    metodo: Mapped[str] = mapped_column(String(30))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    venta: Mapped["Venta"] = relationship(back_populates="pago")
    transaccion: Mapped["Transaccion | None"] = relationship(back_populates="pago")


class Transaccion(Base):
    __tablename__ = "transaccion"

    id: Mapped[int] = mapped_column(primary_key=True)
    pago_id: Mapped[int] = mapped_column(ForeignKey("pago.id"), unique=True)
    pasarela: Mapped[str] = mapped_column(String(30))
    referencia_externa: Mapped[str | None] = mapped_column(String(150))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    pago: Mapped["Pago"] = relationship(back_populates="transaccion")
