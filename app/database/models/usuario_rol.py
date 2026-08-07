from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.database.models.usuario import Usuario


class UsuarioRol(Base):
    __tablename__ = "usuarios_roles"
    __table_args__ = (
        UniqueConstraint("usuario_id", "rol", "perfil", name="uq_usuarios_roles_usuario_rol_perfil"),
    )

    id_rol: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    perfil: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    usuario: Mapped["Usuario"] = relationship(
        back_populates="roles",
    )
