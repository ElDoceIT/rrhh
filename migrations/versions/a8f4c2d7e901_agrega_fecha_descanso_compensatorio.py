"""agrega fecha prevista para descanso compensatorio

Revision ID: a8f4c2d7e901
Revises: c7e3a9b5d102
Create Date: 2026-10-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8f4c2d7e901"
down_revision: Union[str, Sequence[str], None] = "c7e3a9b5d102"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "horas_extras",
        sa.Column("fecha_descanso_compensatorio", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("horas_extras", "fecha_descanso_compensatorio")
