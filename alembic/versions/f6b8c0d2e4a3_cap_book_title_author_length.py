"""cap_book_title_author_length

Revision ID: f6b8c0d2e4a3
Revises: e5f7a9c1b3d2
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f6b8c0d2e4a3'
down_revision: Union[str, Sequence[str], None] = 'e5f7a9c1b3d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('books', 'title', type_=sa.String(255), existing_nullable=False)
    op.alter_column('books', 'author', type_=sa.String(255), existing_nullable=False)


def downgrade() -> None:
    op.alter_column('books', 'title', type_=sa.String(), existing_nullable=False)
    op.alter_column('books', 'author', type_=sa.String(), existing_nullable=False)
