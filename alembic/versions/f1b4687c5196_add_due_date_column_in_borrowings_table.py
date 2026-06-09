"""add due date column in borrowings table

Revision ID: f1b4687c5196
Revises: 32c1f3fba402
Create Date: 2026-06-07 05:56:32.477072

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1b4687c5196'
down_revision: Union[str, Sequence[str], None] = '32c1f3fba402'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    # Step 1: Add the column as nullable first
    op.add_column('borrowings', sa.Column('due_date', sa.DateTime(), nullable=True))
   
   # Step 2: Backfill existing rows — set due_date = borrowed_at + 14 days
    op.execute(""" 
            Update borrowings
            Set due_date = borrowed_at + Interval '14 days'
            where due_date is Null
               """
        )
    # Step 3: Now make the column NOT NULL since every row has a value
    op.alter_column('borrowings', 'due_date', nullable= False)

def downgrade() -> None:
    """Downgrade schema."""
   
    op.drop_column('borrowings', 'due_date')
    
