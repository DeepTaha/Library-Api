"""create books and borrowings table

Revision ID: 32dade78b07e
Revises: 
Create Date: 2026-06-05 07:20:07.371342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32dade78b07e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('author', sa.String(), nullable=False),
        sa.Column('total_copies', sa.Integer(), nullable=False),
        sa.Column('available_copies', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_books_id'), 'books', ['id'], unique=False)
    op.create_table('borrowings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('user_name', sa.String(), nullable=False),
        sa.Column('borrowed_at', sa.DateTime(), nullable=False),
        sa.Column('returned_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_borrowings_id'), 'borrowings', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_borrowings_id'), table_name='borrowings')
    op.drop_table('borrowings')
    op.drop_index(op.f('ix_books_id'), table_name='books')
    op.drop_table('books')