"""agrega TODOS a los tipos de dia permitidos

Revision ID: b72e5d9f3a01
Revises: a61f4c8d2e90
Create Date: 2026-08-10
"""

from typing import Sequence, Union

from alembic import op


revision: str = "b72e5d9f3a01"
down_revision: Union[str, Sequence[str], None] = "a61f4c8d2e90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("chk_reglas_tipo_dia", "reglas_horas", type_="check")
    op.create_check_constraint(
        "chk_reglas_tipo_dia",
        "reglas_horas",
        "tipo_dia IN ('HABIL', 'FERIADO', 'FRANCO', 'TODOS')",
    )


def downgrade() -> None:
    op.drop_constraint("chk_reglas_tipo_dia", "reglas_horas", type_="check")
    op.create_check_constraint(
        "chk_reglas_tipo_dia",
        "reglas_horas",
        "tipo_dia IN ('HABIL', 'FERIADO', 'FRANCO')",
    )
