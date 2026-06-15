"""add_unique_active_borrowing_per_user_book

Revision ID: d2e4f6a8b0c1
Revises: a3c5e7f9b1d2
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'd2e4f6a8b0c1'
down_revision: Union[str, Sequence[str], None] = 'a3c5e7f9b1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE UNIQUE INDEX uq_active_borrowing_per_user_book
        ON borrowings (user_id, book_id)
        WHERE returned_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_active_borrowing_per_user_book")
