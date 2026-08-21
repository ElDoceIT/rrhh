"""agrega devuelve a feriados

Revision ID: e31f7a9c2d64
Revises: d94a7f1b5c23
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e31f7a9c2d64"
down_revision: Union[str, Sequence[str], None] = "d94a7f1b5c23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "feriados",
        sa.Column(
            "devuelve",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("feriados", "devuelve")
