from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.mysql import INTEGER

from app.database.connection import Base

if TYPE_CHECKING:
    from app.database.models.usuario import Usuario


class HoraExtra(Base):
    __tablename__ = "horas_extras"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )

    fecha: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    hora_inicio: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    hora_fin: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    horas_totales: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    cantidad: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )

    concepto_excepcional_id: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("conceptos_excepcionales.id_concepto_excepcional"),
        nullable=True,
        index=True,
    )

    concepto_excepcional_nombre: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
    )

    tipo_dia: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    tipo_hora: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    horas_nocturnas: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        default=Decimal("0.00"),
    )

    tipo_registro: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="HORAS",
    )

    solicita_reintegro: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    observacion_rechazo: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDIENTE",
    )

    aprobado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )

    fecha_carga: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    fecha_resolucion: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    usuario: Mapped["Usuario"] = relationship(
        back_populates="horas_extras",
        foreign_keys=[usuario_id],
    )

    aprobador: Mapped["Usuario | None"] = relationship(
        back_populates="horas_aprobadas",
        foreign_keys=[aprobado_por],
    )
