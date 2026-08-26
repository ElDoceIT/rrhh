"""permite jornadas que cruzan medianoche

Revision ID: f47b2a8d6c10
Revises: e31f7a9c2d64
Create Date: 2026-08-26
"""

from typing import Sequence, Union

from alembic import op


revision: str = "f47b2a8d6c10"
down_revision: Union[str, Sequence[str], None] = "e31f7a9c2d64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("chk_horario_mismo_dia", "horas_extras", type_="check")
    op.create_check_constraint(
        "chk_horario_mismo_dia",
        "horas_extras",
        "tipo_registro <> 'HORAS' OR hora_fin > hora_inicio",
    )


def downgrade() -> None:
    op.drop_constraint("chk_horario_mismo_dia", "horas_extras", type_="check")
    op.create_check_constraint(
        "chk_horario_mismo_dia",
        "horas_extras",
        "hora_fin > hora_inicio",
    )
