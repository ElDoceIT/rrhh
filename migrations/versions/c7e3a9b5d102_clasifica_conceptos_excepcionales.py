"""clasifica conceptos excepcionales y agrega permiso de cargas FC

Revision ID: c7e3a9b5d102
Revises: f93b7a1c2d40
Create Date: 2026-10-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7e3a9b5d102"
down_revision: Union[str, Sequence[str], None] = "f93b7a1c2d40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conceptos_excepcionales",
        sa.Column("codigo", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "conceptos_excepcionales",
        sa.Column(
            "tipo", sa.String(length=20), nullable=False,
            server_default="CARGA_MANUAL",
        ),
    )
    op.create_unique_constraint(
        "uq_conceptos_excepcionales_codigo", "conceptos_excepcionales", ["codigo"],
    )
    op.execute(sa.text(
        "INSERT INTO conceptos_excepcionales "
        "(nombre, codigo, tipo, descripcion, activo, requiere_observacion, fecha_creacion) "
        "VALUES ('Habilitación de cargas FC', 'PERMISO_CARGAS_FC', 'PERMISO', "
        "'Permite cargar horas extras y franco o feriado trabajado a usuarios del convenio FC.', "
        "1, 0, NOW())"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "DELETE FROM usuarios_conceptos_excepcionales "
        "WHERE concepto_excepcional_id IN ("
        "SELECT id_concepto_excepcional FROM conceptos_excepcionales "
        "WHERE codigo = 'PERMISO_CARGAS_FC')"
    ))
    op.execute(sa.text(
        "DELETE FROM conceptos_excepcionales WHERE codigo = 'PERMISO_CARGAS_FC'"
    ))
    op.drop_constraint(
        "uq_conceptos_excepcionales_codigo", "conceptos_excepcionales", type_="unique",
    )
    op.drop_column("conceptos_excepcionales", "tipo")
    op.drop_column("conceptos_excepcionales", "codigo")
