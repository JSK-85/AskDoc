"""Initial tables

Revision ID: 8901fc3dc5b1
Revises: 
Create Date: 2026-05-22 18:16:51.447177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8901fc3dc5b1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'INGESTING', 'DONE', 'FAILED', name='docstatus'), nullable=False),
        sa.Column('total_chunks', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'chunks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('faiss_idx', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('chunks')
    op.drop_table('documents')
    op.execute('DROP TYPE docstatus;')
