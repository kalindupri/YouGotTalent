"""add billing lifecycle: cancel-at-period-end, retention discount, dunning, payments

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8
Create Date: 2026-07-31T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c3d4e5f6a7b9'
down_revision: Union[str, None] = 'b2c3d4e5f6a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('subscriptions', sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('subscriptions', sa.Column('canceled_requested_at', sa.DateTime(timezone=True), nullable=True))

    cancellation_reason_enum = sa.Enum(
        'TOO_EXPENSIVE', 'NOT_USING_ENOUGH', 'MISSING_FEATURES', 'SWITCHING_PLATFORM', 'TEMPORARY_PAUSE', 'OTHER',
        name='cancellation_reason',
    )
    cancellation_reason_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('subscriptions', sa.Column('cancellation_reason_category', cancellation_reason_enum, nullable=True))
    op.add_column('subscriptions', sa.Column('cancellation_reason_detail', sa.Text(), nullable=True))
    op.add_column('subscriptions', sa.Column('retention_offer_used', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('subscriptions', sa.Column('discount_percent', sa.Integer(), nullable=True))
    op.add_column('subscriptions', sa.Column('discount_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('subscriptions', sa.Column('past_due_since', sa.DateTime(timezone=True), nullable=True))
    op.add_column('subscriptions', sa.Column('past_due_reminder_sent_at', sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        'subscription_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount_lkr', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('SUCCEEDED', 'FAILED', 'REFUNDED', name='payment_status'), nullable=False),
        sa.Column('gateway', postgresql.ENUM('MOCK', 'PAYHERE', 'STRIPE', name='payment_gateway_name', create_type=False), nullable=False),
        sa.Column('gateway_reference', sa.String(length=200), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_subscription_payments_subscription_id', 'subscription_payments', ['subscription_id'])


def downgrade() -> None:
    op.drop_index('ix_subscription_payments_subscription_id', table_name='subscription_payments')
    op.drop_table('subscription_payments')
    sa.Enum(name='payment_status').drop(op.get_bind(), checkfirst=True)

    op.drop_column('subscriptions', 'past_due_reminder_sent_at')
    op.drop_column('subscriptions', 'past_due_since')
    op.drop_column('subscriptions', 'discount_expires_at')
    op.drop_column('subscriptions', 'discount_percent')
    op.drop_column('subscriptions', 'retention_offer_used')
    op.drop_column('subscriptions', 'cancellation_reason_detail')
    op.drop_column('subscriptions', 'cancellation_reason_category')
    sa.Enum(name='cancellation_reason').drop(op.get_bind(), checkfirst=True)
    op.drop_column('subscriptions', 'canceled_requested_at')
    op.drop_column('subscriptions', 'cancel_at_period_end')
