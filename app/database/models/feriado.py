from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Feriado(Base):
    __tablename__ = "feriados"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    fecha: Mapped[date] = mapped_column(
        Date,
        unique=True,
        nullable=False,
    )

    observacion: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
