"""add_password_reset_tokens_table

Revision ID: f4a9b2c3d1e0
Revises: e001e88c11d7
Create Date: 2026-06-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f4a9b2c3d1e0'
down_revision: Union[str, Sequence[str], None] = 'e001e88c11d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'password_reset_tokens',
        sa.Column('token', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('ix_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])


def downgrade() -> None:
    op.drop_index('ix_password_reset_tokens_expires_at', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
