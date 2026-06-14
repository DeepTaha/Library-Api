"""add_blacklisted_tokens_table

Revision ID: e001e88c11d7
Revises: c9f3a2d1e847
Create Date: 2026-06-12 03:14:37.402113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e001e88c11d7'
down_revision: Union[str, Sequence[str], None] = 'c9f3a2d1e847'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'blacklisted_tokens',
        sa.Column('jti', sa.String(36), primary_key=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        if_not_exists=True,
    )
    op.create_index('ix_blacklisted_tokens_expires_at', 'blacklisted_tokens', ['expires_at'], if_not_exists=True)
    op.alter_column('borrowings', 'due_date',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('borrowings', 'due_date',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False)
    op.drop_index('ix_blacklisted_tokens_expires_at', table_name='blacklisted_tokens')
    op.drop_table('blacklisted_tokens')
