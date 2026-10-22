"""agrega concepto automatico switcher nocturnidad

Revision ID: f1a7c9d2e604
Revises: c6d8f31a9e42
Create Date: 2026-10-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a7c9d2e604"
down_revision: Union[str, Sequence[str], None] = "c6d8f31a9e42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text(
        "INSERT INTO conceptos_excepcionales "
        "(nombre, codigo, tipo, cantidad_predeterminada, tipo_hora_destino, "
        "requiere_autorizacion, descripcion, activo, requiere_observacion, "
        "creado_por, fecha_creacion) "
        "SELECT 'switcher_nocturnidad', 'SWITCHER_NOCTURNIDAD', "
        "'DERIVADO_NOCTURNIDAD', NULL, NULL, 1, "
        "'Genera automáticamente una unidad por cada hora nocturna registrada.', "
        "1, 0, NULL, CURRENT_TIMESTAMP "
        "WHERE NOT EXISTS ("
        "SELECT 1 FROM conceptos_excepcionales "
        "WHERE codigo = 'SWITCHER_NOCTURNIDAD'"
        ")"
    ))


def downgrade() -> None:
    # Se conserva el concepto desactivado para no perder asignaciones ni cargas
    # históricas que pudieran haberse generado después del upgrade.
    op.execute(sa.text(
        "UPDATE conceptos_excepcionales SET activo = 0 "
        "WHERE codigo = 'SWITCHER_NOCTURNIDAD'"
    ))
