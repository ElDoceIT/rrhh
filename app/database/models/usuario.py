from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.database.models.hora_extra import HoraExtra
    from app.database.models.tipo_contratacion import TipoContratacion
    from app.database.models.usuario_rol import UsuarioRol


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    legajo: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    apellido: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    correo: Mapped[str | None] = mapped_column(
        String(150),
        unique=True,
        nullable=True,
    )

    convenio: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    id_tipo_contratacion: Mapped[int | None] = mapped_column(
        ForeignKey("tipo_contratacion.id_tipo_contratacion"),
        nullable=True,
        index=True,
    )

    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    origen: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="LOCAL",
    )

    status: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    roles: Mapped[list["UsuarioRol"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    tipo_contratacion: Mapped["TipoContratacion | None"] = relationship(
        back_populates="usuarios",
    )

    horas_extras: Mapped[list["HoraExtra"]] = relationship(
        back_populates="usuario",
        foreign_keys="HoraExtra.usuario_id",
    )

    horas_aprobadas: Mapped[list["HoraExtra"]] = relationship(
        back_populates="aprobador",
        foreign_keys="HoraExtra.aprobado_por",
    )
