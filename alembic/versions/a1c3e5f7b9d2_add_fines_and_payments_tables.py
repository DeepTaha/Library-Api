"""add_fines_and_payments_tables

Revision ID: a1c3e5f7b9d2
Revises: f6b8c0d2e4a3
Create Date: 2026-06-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

revision: str = 'a1c3e5f7b9d2'
down_revision: Union[str, Sequence[str], None] = 'f6b8c0d2e4a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create PostgreSQL enum types via raw SQL.
    # We do this separately so op.create_table does not try to create them again.
    op.execute("CREATE TYPE finestatus AS ENUM ('pending', 'paid', 'waived')")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('pending', 'completed', 'failed')")

    # fines table
    op.create_table(
        'fines',
        sa.Column('id',           sa.Integer(),                nullable=False),
        sa.Column('borrowing_id', sa.Integer(),                nullable=False),
        sa.Column('user_id',      sa.Integer(),                nullable=False),
        sa.Column('days_overdue', sa.Integer(),                nullable=False),
        sa.Column('amount',       sa.Integer(),                nullable=False),
        sa.Column('status',       PgEnum('pending', 'paid', 'waived', name='finestatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('created_at',   sa.DateTime(timezone=True),  nullable=False, server_default=sa.text('now()')),
        sa.Column('paid_at',      sa.DateTime(timezone=True),  nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['borrowing_id'], ['borrowings.id']),
        sa.ForeignKeyConstraint(['user_id'],      ['users.id']),
        sa.UniqueConstraint('borrowing_id', name='uq_fine_borrowing'),
    )
    op.create_index('ix_fines_id',          'fines', ['id'])
    op.create_index('ix_fines_user_status', 'fines', ['user_id', 'status'])

    # payments table — references fines, so created after
    op.create_table(
        'payments',
        sa.Column('id',              sa.Integer(),               nullable=False),
        sa.Column('fine_id',         sa.Integer(),               nullable=False),
        sa.Column('user_id',         sa.Integer(),               nullable=False),
        sa.Column('amount',          sa.Integer(),               nullable=False),
        sa.Column('order_id',        sa.String(64),              nullable=False),
        sa.Column('safepay_tracker', sa.String(128),             nullable=True),
        sa.Column('status',          PgEnum('pending', 'completed', 'failed', name='paymentstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('created_at',      sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at',    sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason',  sa.String(255),             nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fine_id'], ['fines.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.UniqueConstraint('fine_id',  name='uq_payment_fine'),
        sa.UniqueConstraint('order_id', name='uq_payment_order_id'),
    )
    op.create_index('ix_payments_id',      'payments', ['id'])
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])


def downgrade() -> None:
    # Drop in reverse order — payments first because it references fines
    op.drop_index('ix_payments_user_id', table_name='payments')
    op.drop_index('ix_payments_id',      table_name='payments')
    op.drop_table('payments')

    op.drop_index('ix_fines_user_status', table_name='fines')
    op.drop_index('ix_fines_id',          table_name='fines')
    op.drop_table('fines')

    # Drop enums last — cannot drop while any column still uses them
    op.execute("DROP TYPE paymentstatus")
    op.execute("DROP TYPE finestatus")
