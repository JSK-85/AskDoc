"""Add query logs

Revision ID: decaf6dc6e60
Revises: 8901fc3dc5b1
Create Date: 2026-05-23 13:20:49.470367

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'decaf6dc6e60'
down_revision: Union[str, Sequence[str], None] = '8901fc3dc5b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'query_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('feedback', sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('query_logs')

