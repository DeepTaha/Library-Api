"""add is_suspended to users

Revision ID: c9f3a2d1e847
Revises: b7d4e1f2c309
Create Date: 2026-06-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9f3a2d1e847'
down_revision: Union[str, Sequence[str], None] = 'b7d4e1f2c309'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('users', 'is_suspended')
