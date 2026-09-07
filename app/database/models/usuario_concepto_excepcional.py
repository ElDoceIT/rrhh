from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class UsuarioConceptoExcepcional(Base):
    __tablename__ = "usuarios_conceptos_excepcionales"

    id_asignacion: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True,
    )
    usuario_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), ForeignKey("usuarios.id"), nullable=False, index=True,
    )
    concepto_excepcional_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("conceptos_excepcionales.id_concepto_excepcional"),
        nullable=False,
        index=True,
    )
    fecha_desde: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    observacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    asignado_por: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True,
    )
    fecha_asignacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now,
    )

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    asignador = relationship("Usuario", foreign_keys=[asignado_por])
    concepto = relationship("ConceptoExcepcional", back_populates="asignaciones")
