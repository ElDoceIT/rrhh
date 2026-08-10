"""permite varias reglas por convenio y tipo de dia

Revision ID: a61f4c8d2e90
Revises: f2b6d04e8a19
Create Date: 2026-08-10
"""

from typing import Sequence, Union

from alembic import op


revision: str = "a61f4c8d2e90"
down_revision: Union[str, Sequence[str], None] = "f2b6d04e8a19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_regla_convenio_tipo_dia",
        "reglas_horas",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_regla_convenio_tipo_dia",
        "reglas_horas",
        ["convenio", "tipo_dia"],
    )
