"""add age restriction fields

Revision ID: a1b2c3d4e5f6
Revises: e3f7a9b2c841
Create Date: 2026-06-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e3f7a9b2c841'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('books', sa.Column('is_age_restricted', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'date_of_birth')
    op.drop_column('books', 'is_age_restricted')
