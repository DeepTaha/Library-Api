"""add_extension_count_to_borrowings

Revision ID: e5f7a9c1b3d2
Revises: d2e4f6a8b0c1
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e5f7a9c1b3d2'
down_revision: Union[str, Sequence[str], None] = 'd2e4f6a8b0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'borrowings',
        sa.Column('extension_count', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('borrowings', 'extension_count')
