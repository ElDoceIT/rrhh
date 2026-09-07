from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class ConceptoExcepcional(Base):
    __tablename__ = "conceptos_excepcionales"

    id_concepto_excepcional: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True,
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requiere_observacion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_por: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now,
    )

    asignaciones: Mapped[list["UsuarioConceptoExcepcional"]] = relationship(
        back_populates="concepto",
    )


from app.database.models.usuario_concepto_excepcional import UsuarioConceptoExcepcional
