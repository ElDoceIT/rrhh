"""crea tabla feriados

Revision ID: f2b6d04e8a19
Revises: e7a3b19c5d42
Create Date: 2026-07-31
"""

from datetime import date
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2b6d04e8a19"
down_revision: Union[str, Sequence[str], None] = "e7a3b19c5d42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feriados",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("observacion", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fecha", name="uq_feriados_fecha"),
    )
    feriados = sa.table(
        "feriados",
        sa.column("fecha", sa.Date()),
        sa.column("observacion", sa.String()),
    )
    op.bulk_insert(feriados, [
        {"fecha": date(2026, 1, 1), "observacion": "Año Nuevo"},
        {"fecha": date(2026, 2, 16), "observacion": "Carnaval"},
        {"fecha": date(2026, 2, 17), "observacion": "Carnaval"},
        {"fecha": date(2026, 3, 24), "observacion": "Día Nacional de la Memoria por la Verdad y la Justicia"},
        {"fecha": date(2026, 4, 2), "observacion": "Día del Veterano y de los Caídos en la Guerra de Malvinas"},
        {"fecha": date(2026, 4, 3), "observacion": "Viernes Santo"},
        {"fecha": date(2026, 5, 1), "observacion": "Día del Trabajador"},
        {"fecha": date(2026, 5, 25), "observacion": "Día de la Revolución de Mayo"},
        {"fecha": date(2026, 6, 15), "observacion": "Paso a la Inmortalidad del General Martín Miguel de Güemes"},
        {"fecha": date(2026, 6, 20), "observacion": "Paso a la Inmortalidad del General Manuel Belgrano"},
        {"fecha": date(2026, 7, 9), "observacion": "Día de la Independencia"},
        {"fecha": date(2026, 8, 17), "observacion": "Paso a la Inmortalidad del General José de San Martín"},
        {"fecha": date(2026, 10, 12), "observacion": "Día de la Raza"},
        {"fecha": date(2026, 11, 23), "observacion": "Día de la Soberanía Nacional"},
        {"fecha": date(2026, 12, 8), "observacion": "Inmaculada Concepción de María"},
        {"fecha": date(2026, 12, 25), "observacion": "Navidad"},
        {"fecha": date(2027, 1, 1), "observacion": "Año Nuevo"},
    ])


def downgrade() -> None:
    op.drop_table("feriados")
