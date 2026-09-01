from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.p1_seguridad import Usuario


class Ciudad(Base):
    __tablename__ = "ciudad"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    departamento: Mapped[str] = mapped_column(String(100))

    sucursales: Mapped[list["Sucursal"]] = relationship(back_populates="ciudad")


class Sucursal(Base):
    __tablename__ = "sucursal"

    id: Mapped[int] = mapped_column(primary_key=True)
    ciudad_id: Mapped[int] = mapped_column(ForeignKey("ciudad.id"))
    nombre: Mapped[str] = mapped_column(String(150))
    direccion: Mapped[str] = mapped_column(String(255))
    horario_atencion: Mapped[str | None] = mapped_column(String(100))
    telefono: Mapped[str | None] = mapped_column(String(30))
    estado: Mapped[str] = mapped_column(String(20), default="activa")
    fecha_creacion: Mapped[date] = mapped_column(Date, default=date.today)

    ciudad: Mapped["Ciudad"] = relationship(back_populates="sucursales")
    empleados: Mapped[list["Empleado"]] = relationship(back_populates="sucursal")
    inventarios: Mapped[list["Inventario"]] = relationship(back_populates="sucursal")
    reservas: Mapped[list["Reserva"]] = relationship(back_populates="sucursal")
    ventas: Mapped[list["Venta"]] = relationship(back_populates="sucursal")


class Cliente(Usuario):
    __tablename__ = "cliente"

    id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), primary_key=True)
    telefono: Mapped[str | None] = mapped_column(String(30))
    direccion: Mapped[str | None] = mapped_column(String(255))

    reservas: Mapped[list["Reserva"]] = relationship(back_populates="cliente")
    carritos: Mapped[list["Carrito"]] = relationship(back_populates="cliente")
    ventas: Mapped[list["Venta"]] = relationship(back_populates="cliente")
    notificaciones: Mapped[list["Notificacion"]] = relationship(back_populates="cliente")
    recomendaciones: Mapped[list["Recomendacion"]] = relationship(back_populates="cliente")
    chats: Mapped[list["Chatbot"]] = relationship(back_populates="cliente")

    __mapper_args__ = {"polymorphic_identity": "cliente"}
