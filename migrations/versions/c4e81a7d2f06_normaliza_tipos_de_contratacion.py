"""normaliza tipos de contratacion

Revision ID: c4e81a7d2f06
Revises: 9d8c4a2f7b31
Create Date: 2026-07-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e81a7d2f06"
down_revision: Union[str, Sequence[str], None] = "9d8c4a2f7b31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tipo_contratacion",
        sa.Column("id_tipo_contratacion", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("contratacion", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id_tipo_contratacion"),
        sa.UniqueConstraint("contratacion", name="uq_tipo_contratacion_nombre"),
    )

    tabla = sa.table(
        "tipo_contratacion",
        sa.column("id_tipo_contratacion", sa.Integer()),
        sa.column("contratacion", sa.String()),
    )
    op.bulk_insert(tabla, [
        {"id_tipo_contratacion": 1, "contratacion": "Nómina"},
        {"id_tipo_contratacion": 2, "contratacion": "Monotributo"},
        {"id_tipo_contratacion": 3, "contratacion": "Consultora"},
    ])

    op.add_column(
        "usuarios",
        sa.Column("id_tipo_contratacion", sa.Integer(), nullable=True),
    )
    op.execute("""
        UPDATE usuarios
        SET id_tipo_contratacion = CASE LOWER(TRIM(contratacion))
            WHEN 'nomina' THEN 1
            WHEN 'nómina' THEN 1
            WHEN 'monotributo' THEN 2
            WHEN 'consultora' THEN 3
            ELSE NULL
        END
    """)
    op.create_index(
        "ix_usuarios_id_tipo_contratacion",
        "usuarios",
        ["id_tipo_contratacion"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_usuarios_tipo_contratacion",
        "usuarios",
        "tipo_contratacion",
        ["id_tipo_contratacion"],
        ["id_tipo_contratacion"],
        onupdate="CASCADE",
        ondelete="RESTRICT",
    )
    op.drop_column("usuarios", "contratacion")


def downgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("contratacion", sa.String(length=100), nullable=True),
    )
    op.execute("""
        UPDATE usuarios AS u
        INNER JOIN tipo_contratacion AS tc
            ON tc.id_tipo_contratacion = u.id_tipo_contratacion
        SET u.contratacion = tc.contratacion
    """)
    op.drop_constraint("fk_usuarios_tipo_contratacion", "usuarios", type_="foreignkey")
    op.drop_index("ix_usuarios_id_tipo_contratacion", table_name="usuarios")
    op.drop_column("usuarios", "id_tipo_contratacion")
    op.drop_table("tipo_contratacion")
