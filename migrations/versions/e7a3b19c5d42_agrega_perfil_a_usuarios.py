"""agrega perfil a usuarios

Revision ID: e7a3b19c5d42
Revises: c4e81a7d2f06
Create Date: 2026-07-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7a3b19c5d42"
down_revision: Union[str, Sequence[str], None] = "c4e81a7d2f06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column(
            "perfil",
            sa.String(length=20),
            nullable=False,
            server_default="USUARIO",
        ),
    )
    op.create_check_constraint(
        "ck_usuarios_perfil",
        "usuarios",
        "perfil IN ('USUARIO', 'JEFE')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_usuarios_perfil", "usuarios", type_="check")
    op.drop_column("usuarios", "perfil")
