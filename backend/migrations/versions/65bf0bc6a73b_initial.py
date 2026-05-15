"""initial

Revision ID: 65bf0bc6a73b
Revises: 
Create Date: 2026-05-14 22:36:31.146670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '65bf0bc6a73b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # TEXT and AutoString are equivalent — these are no-ops on SQLite,
    # but the import is needed so Alembic can resolve the type on PostgreSQL.
    with op.batch_alter_table('evento', schema=None) as batch_op:
        batch_op.alter_column('bairro',
               existing_type=sa.TEXT(),
               type_=sqlmodel.sql.sqltypes.AutoString(),
               existing_nullable=True)
        batch_op.alter_column('imagem_url',
               existing_type=sa.TEXT(),
               type_=sqlmodel.sql.sqltypes.AutoString(),
               existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('evento', schema=None) as batch_op:
        batch_op.alter_column('imagem_url',
               existing_type=sqlmodel.sql.sqltypes.AutoString(),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('bairro',
               existing_type=sqlmodel.sql.sqltypes.AutoString(),
               type_=sa.TEXT(),
               existing_nullable=True)
