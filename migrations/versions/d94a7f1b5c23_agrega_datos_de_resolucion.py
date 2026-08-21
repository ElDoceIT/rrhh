"""agrega observacion de rechazo y fecha de resolucion

Revision ID: d94a7f1b5c23
Revises: c83f6e0a4b12
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d94a7f1b5c23"
down_revision: Union[str, Sequence[str], None] = "c83f6e0a4b12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "horas_extras",
        sa.Column("observacion_rechazo", sa.Text(), nullable=True),
    )
    op.add_column(
        "horas_extras",
        sa.Column("fecha_resolucion", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("horas_extras", "fecha_resolucion")
    op.drop_column("horas_extras", "observacion_rechazo")
