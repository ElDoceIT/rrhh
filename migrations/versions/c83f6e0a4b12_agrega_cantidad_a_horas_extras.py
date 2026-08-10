"""agrega cantidad para otras cargas

Revision ID: c83f6e0a4b12
Revises: b72e5d9f3a01
Create Date: 2026-08-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c83f6e0a4b12"
down_revision: Union[str, Sequence[str], None] = "b72e5d9f3a01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "horas_extras",
        sa.Column("cantidad", sa.Numeric(precision=8, scale=2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("horas_extras", "cantidad")
