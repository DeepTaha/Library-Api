"""adding genre column to books

Revision ID: 5c088a1d1b4a
Revises: 32dade78b07e
Create Date: 2026-06-05 07:46:49.958905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c088a1d1b4a'
down_revision: Union[str, Sequence[str], None] = '32dade78b07e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('books',sa.Column('genre', sa.String(length=100), nullable=True))
  


def downgrade() -> None:
    op.drop_column('books','genre')
   