"""add document summary column

Revision ID: b5e8a2f1d3c7
Revises: decaf6dc6e60
Create Date: 2026-05-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5e8a2f1d3c7'
down_revision: Union[str, None] = ('a3b7f1e2c4d6', 'decaf6dc6e60')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('summary', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('documents', 'summary')
