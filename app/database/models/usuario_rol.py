from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.database.models.usuario import Usuario


class UsuarioRol(Base):
    __tablename__ = "usuarios_roles"

    id_rol: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    rol: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    perfil: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    usuarios: Mapped[list["Usuario"]] = relationship(
        back_populates="rol",
    )