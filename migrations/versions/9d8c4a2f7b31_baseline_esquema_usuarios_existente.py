"""baseline del esquema de usuarios existente

Revision ID: 9d8c4a2f7b31
Revises:
Create Date: 2026-07-31

Esta revisión restaura el punto de partida del historial actual. El esquema
correspondiente ya existe en la base de desarrollo, por lo que no ejecuta DDL.
"""

from typing import Sequence, Union


revision: str = "9d8c4a2f7b31"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
