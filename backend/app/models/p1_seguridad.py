from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

rol_permiso = Table(
    "rol_permiso",
    Base.metadata,
    Column("rol_id", ForeignKey("rol.id"), primary_key=True),
    Column("permiso_id", ForeignKey("permiso.id"), primary_key=True),
)


class Rol(Base):
    __tablename__ = "rol"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")
    permisos: Mapped[list["Permiso"]] = relationship(secondary=rol_permiso, back_populates="roles")


class Permiso(Base):
    __tablename__ = "permiso"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))

    roles: Mapped[list["Rol"]] = relationship(secondary=rol_permiso, back_populates="permisos")


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), default="activo")
    fecha_registro: Mapped[date] = mapped_column(Date, default=date.today)
    tipo: Mapped[str] = mapped_column(String(30))
    metodo_registro: Mapped[str] = mapped_column(String(20), default="email")

    rol_id: Mapped[int | None] = mapped_column(ForeignKey("rol.id"))
    rol: Mapped["Rol | None"] = relationship(back_populates="usuarios")

    # session_id identifica la sesion activa: cada login la reemplaza, asi
    # que un token viejo (de otro dispositivo) deja de pasar la verificacion.
    session_id: Mapped[str | None] = mapped_column(String(64))
    reset_code_hash: Mapped[str | None] = mapped_column(String(255))
    reset_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    bitacoras: Mapped[list["Bitacora"]] = relationship(back_populates="usuario")

    __mapper_args__ = {
        "polymorphic_identity": "usuario",
        "polymorphic_on": "tipo",
    }


class Bitacora(Base):
    __tablename__ = "bitacora"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    accion: Mapped[str] = mapped_column(String(100))
    entidad_afectada: Mapped[str] = mapped_column(String(100))
    entidad_id: Mapped[int | None] = mapped_column()
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    detalle: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))

    usuario: Mapped["Usuario"] = relationship(back_populates="bitacoras")


class Empleado(Usuario):
    __tablename__ = "empleado"

    id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), primary_key=True)
    sucursal_id: Mapped[int | None] = mapped_column(ForeignKey("sucursal.id"))

    sucursal: Mapped["Sucursal | None"] = relationship(back_populates="empleados")
    movimientos_inventario: Mapped[list["MovimientoInventario"]] = relationship(back_populates="empleado")
    reportes: Mapped[list["Reporte"]] = relationship(back_populates="empleado")

    __mapper_args__ = {"polymorphic_identity": "empleado"}


class Administrador(Empleado):
    __tablename__ = "administrador"

    id: Mapped[int] = mapped_column(ForeignKey("empleado.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "administrador"}


class EncargadoSucursal(Empleado):
    __tablename__ = "encargado_sucursal"

    id: Mapped[int] = mapped_column(ForeignKey("empleado.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "encargado_sucursal"}


class Cajero(Empleado):
    __tablename__ = "cajero"

    id: Mapped[int] = mapped_column(ForeignKey("empleado.id"), primary_key=True)

    ventas_atendidas: Mapped[list["VentaPresencial"]] = relationship(back_populates="cajero")

    __mapper_args__ = {"polymorphic_identity": "cajero"}
