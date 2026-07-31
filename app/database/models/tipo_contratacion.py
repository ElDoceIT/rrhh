from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.database.models.usuario import Usuario


class TipoContratacion(Base):
    __tablename__ = "tipo_contratacion"

    id_tipo_contratacion: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    contratacion: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    usuarios: Mapped[list["Usuario"]] = relationship(
        back_populates="tipo_contratacion",
    )
