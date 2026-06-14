"""add_tokens_valid_from_to_users

Revision ID: a3c5e7f9b1d2
Revises: f4a9b2c3d1e0
Create Date: 2026-06-12 13:00:00.000000

"""
from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision: str = 'a3c5e7f9b1d2'
down_revision: Union[str, Sequence[str], None] = 'f4a9b2c3d1e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'tokens_valid_from',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'tokens_valid_from')
