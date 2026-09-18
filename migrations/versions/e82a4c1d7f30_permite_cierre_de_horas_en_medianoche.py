"""permite cerrar un tramo de horas en medianoche

Revision ID: e82a4c1d7f30
Revises: d31e7a9c4f62
Create Date: 2026-09-18
"""

from typing import Sequence, Union

from alembic import op


revision: str = "e82a4c1d7f30"
down_revision: Union[str, Sequence[str], None] = "d31e7a9c4f62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "chk_horario_mismo_dia", "horas_extras", type_="check",
    )
    op.create_check_constraint(
        "chk_horario_mismo_dia",
        "horas_extras",
        "tipo_registro <> 'HORAS' "
        "OR hora_fin > hora_inicio "
        "OR (hora_fin = '00:00:00' AND hora_inicio > '00:00:00')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "chk_horario_mismo_dia", "horas_extras", type_="check",
    )
    op.create_check_constraint(
        "chk_horario_mismo_dia",
        "horas_extras",
        "tipo_registro <> 'HORAS' OR hora_fin > hora_inicio",
    )
