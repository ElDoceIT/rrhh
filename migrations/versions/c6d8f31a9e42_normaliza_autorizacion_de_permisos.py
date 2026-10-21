"""normaliza autorizacion de conceptos de permiso

Revision ID: c6d8f31a9e42
Revises: b4c9e12a7d63
Create Date: 2026-10-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6d8f31a9e42"
down_revision: Union[str, Sequence[str], None] = "b4c9e12a7d63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text(
        "UPDATE conceptos_excepcionales "
        "SET requiere_autorizacion = 0 WHERE tipo = 'PERMISO'"
    ))


def downgrade() -> None:
    # El valor anterior no puede reconstruirse de forma confiable.
    pass
