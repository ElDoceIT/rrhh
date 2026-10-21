"""configura modalidades de carga y precargas

Revision ID: b4c9e12a7d63
Revises: a8f4c2d7e901
Create Date: 2026-10-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4c9e12a7d63"
down_revision: Union[str, Sequence[str], None] = "a8f4c2d7e901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conceptos_excepcionales",
        sa.Column("cantidad_predeterminada", sa.Numeric(8, 2), nullable=True),
    )
    op.add_column(
        "conceptos_excepcionales",
        sa.Column("tipo_hora_destino", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "conceptos_excepcionales",
        sa.Column(
            "requiere_autorizacion",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "usuarios_conceptos_excepcionales",
        sa.Column("cantidad_asignada", sa.Numeric(8, 2), nullable=True),
    )
    op.add_column(
        "reglas_horas",
        sa.Column("modalidad_carga", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "reglas_horas",
        sa.Column("cantidad_predeterminada", sa.Numeric(8, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reglas_horas", "cantidad_predeterminada")
    op.drop_column("reglas_horas", "modalidad_carga")
    op.drop_column("usuarios_conceptos_excepcionales", "cantidad_asignada")
    op.drop_column("conceptos_excepcionales", "requiere_autorizacion")
    op.drop_column("conceptos_excepcionales", "tipo_hora_destino")
    op.drop_column("conceptos_excepcionales", "cantidad_predeterminada")
