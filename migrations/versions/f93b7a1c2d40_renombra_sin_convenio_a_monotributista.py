"""renombra sin convenio a monotributista

Revision ID: f93b7a1c2d40
Revises: e82a4c1d7f30
Create Date: 2026-09-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f93b7a1c2d40"
down_revision: Union[str, Sequence[str], None] = "e82a4c1d7f30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text(
        "UPDATE usuarios SET convenio = 'MONOTRIBUTISTA' "
        "WHERE UPPER(TRIM(convenio)) = 'SIN CONVENIO'"
    ))
    op.execute(sa.text(
        "UPDATE reglas_horas SET convenio = 'MONOTRIBUTISTA' "
        "WHERE UPPER(TRIM(convenio)) = 'SIN CONVENIO'"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "UPDATE usuarios SET convenio = 'SIN CONVENIO' "
        "WHERE UPPER(TRIM(convenio)) = 'MONOTRIBUTISTA'"
    ))
    op.execute(sa.text(
        "UPDATE reglas_horas SET convenio = 'SIN CONVENIO' "
        "WHERE UPPER(TRIM(convenio)) = 'MONOTRIBUTISTA'"
    ))
