"""add file_path and pinned to documents

Revision ID: a3b7f1e2c4d6
Revises: decaf6dc6e60
Create Date: 2026-05-25 16:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b7f1e2c4d6'
down_revision: Union[str, None] = 'decaf6dc6e60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('file_path', sa.String(512), nullable=True))
    op.add_column('documents', sa.Column('pinned', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('documents', 'pinned')
    op.drop_column('documents', 'file_path')
