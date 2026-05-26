"""add latitude longitude to evento

Revision ID: c2d3e4f5a6b7
Revises: b1d2e3f4a5c6
Create Date: 2026-05-25

"""
from alembic import op
import sqlalchemy as sa

revision = 'c2d3e4f5a6b7'
down_revision = 'b1d2e3f4a5c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('evento', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('evento', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('evento', 'longitude')
    op.drop_column('evento', 'latitude')
