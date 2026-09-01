from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Notificacion(Base):
    __tablename__ = "notificacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"))
    canal: Mapped[str] = mapped_column(String(30))
    tipo_evento: Mapped[str] = mapped_column(String(50))
    mensaje: Mapped[str] = mapped_column(Text)
    fecha_envio: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")

    cliente: Mapped["Cliente"] = relationship(back_populates="notificaciones")


class Reporte(Base):
    __tablename__ = "reporte"

    id: Mapped[int] = mapped_column(primary_key=True)
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleado.id"))
    tipo: Mapped[str] = mapped_column(String(50))
    formato: Mapped[str] = mapped_column(String(20))
    fecha_generacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    empleado: Mapped["Empleado"] = relationship(back_populates="reportes")


class Dashboard(Base):
    __tablename__ = "dashboard"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    rol_destino: Mapped[str] = mapped_column(String(50))


class Recomendacion(Base):
    __tablename__ = "recomendacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("producto.id"))
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    origen: Mapped[str] = mapped_column(String(50))
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cliente: Mapped["Cliente"] = relationship(back_populates="recomendaciones")
    producto: Mapped["Producto"] = relationship(back_populates="recomendaciones")


class Chatbot(Base):
    __tablename__ = "chatbot"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"))
    canal: Mapped[str] = mapped_column(String(30))
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime)

    cliente: Mapped["Cliente"] = relationship(back_populates="chats")
