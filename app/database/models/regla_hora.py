from datetime import time

from sqlalchemy import Boolean, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ReglaHora(Base):
    __tablename__ = "reglas_horas"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    convenio: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    tipo_dia: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    tipo_hora: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    hora_nocturna_desde: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    hora_nocturna_hasta: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    permite_reintegro: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )