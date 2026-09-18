"""normaliza el código técnico HABIL

Revision ID: d31e7a9c4f62
Revises: a58c1d9e7b20
Create Date: 2026-09-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d31e7a9c4f62"
down_revision: Union[str, Sequence[str], None] = "a58c1d9e7b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text(
        "UPDATE reglas_horas SET tipo_dia = 'HABIL' "
        "WHERE UPPER(tipo_dia) = 'HÁBIL'"
    ))


def downgrade() -> None:
    # HABIL es el código canónico para todos los convenios; no se reintroduce
    # la variante acentuada al revertir la revisión.
    pass
