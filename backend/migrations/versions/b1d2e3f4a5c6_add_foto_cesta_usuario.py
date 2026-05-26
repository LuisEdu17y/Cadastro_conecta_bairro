"""add foto_url and precisa_cesta_basica to usuario

Revision ID: b1d2e3f4a5c6
Revises: a3f1c9e2b847
Create Date: 2026-05-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'b1d2e3f4a5c6'
down_revision: Union[str, Sequence[str], None] = 'a3f1c9e2b847'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuario', sa.Column('foto_url', sa.String(), nullable=True))
    op.add_column('usuario', sa.Column('precisa_cesta_basica', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('usuario', 'precisa_cesta_basica')
    op.drop_column('usuario', 'foto_url')
