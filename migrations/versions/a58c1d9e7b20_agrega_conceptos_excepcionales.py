"""agrega conceptos excepcionales

Revision ID: a58c1d9e7b20
Revises: f47b2a8d6c10
Create Date: 2026-08-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import mysql


revision: str = "a58c1d9e7b20"
down_revision: Union[str, Sequence[str], None] = "f47b2a8d6c10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    tablas = set(inspector.get_table_names())
    if "conceptos_excepcionales" not in tablas:
        op.create_table(
            "conceptos_excepcionales",
            sa.Column("id_concepto_excepcional", mysql.INTEGER(unsigned=True), primary_key=True, autoincrement=True),
            sa.Column("nombre", sa.String(100), nullable=False),
            sa.Column("descripcion", sa.Text(), nullable=True),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("requiere_observacion", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("creado_por", mysql.INTEGER(unsigned=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
            sa.Column("fecha_creacion", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("nombre", name="uq_conceptos_excepcionales_nombre"),
        )
    if "usuarios_conceptos_excepcionales" not in tablas:
        op.create_table(
            "usuarios_conceptos_excepcionales",
            sa.Column("id_asignacion", mysql.INTEGER(unsigned=True), primary_key=True, autoincrement=True),
            sa.Column("usuario_id", mysql.INTEGER(unsigned=True), sa.ForeignKey("usuarios.id"), nullable=False),
            sa.Column("concepto_excepcional_id", mysql.INTEGER(unsigned=True), sa.ForeignKey("conceptos_excepcionales.id_concepto_excepcional"), nullable=False),
            sa.Column("fecha_desde", sa.Date(), nullable=False),
            sa.Column("fecha_hasta", sa.Date(), nullable=True),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("observacion", sa.Text(), nullable=True),
            sa.Column("asignado_por", mysql.INTEGER(unsigned=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
            sa.Column("fecha_asignacion", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("fecha_hasta IS NULL OR fecha_hasta >= fecha_desde", name="chk_asignacion_fechas"),
            sa.UniqueConstraint("usuario_id", "concepto_excepcional_id", "fecha_desde", name="uq_asignacion_usuario_concepto_desde"),
        )
    columnas_horas = {item["name"] for item in inspect(op.get_bind()).get_columns("horas_extras")}
    if "concepto_excepcional_id" not in columnas_horas:
        op.add_column("horas_extras", sa.Column("concepto_excepcional_id", mysql.INTEGER(unsigned=True), nullable=True))
        op.create_foreign_key("fk_horas_concepto_excepcional", "horas_extras", "conceptos_excepcionales", ["concepto_excepcional_id"], ["id_concepto_excepcional"], ondelete="RESTRICT")
        op.create_index("ix_horas_concepto_excepcional", "horas_extras", ["concepto_excepcional_id"])
    if "concepto_excepcional_nombre" not in columnas_horas:
        op.add_column("horas_extras", sa.Column("concepto_excepcional_nombre", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_constraint("fk_horas_concepto_excepcional", "horas_extras", type_="foreignkey")
    op.drop_index("ix_horas_concepto_excepcional", table_name="horas_extras")
    op.drop_column("horas_extras", "concepto_excepcional_nombre")
    op.drop_column("horas_extras", "concepto_excepcional_id")
    op.drop_table("usuarios_conceptos_excepcionales")
    op.drop_table("conceptos_excepcionales")
