"""add subscriptions

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-07-31T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'b2c3d4e5f6a8'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('talent_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('talent_profiles.id', ondelete='CASCADE'), nullable=True),
        sa.Column('recruiter_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recruiter_profiles.id', ondelete='CASCADE'), nullable=True),
        sa.Column('plan', sa.Enum('TALENT_PREMIUM', 'RECRUITER_PREMIUM', name='subscription_plan'), nullable=False),
        sa.Column('billing_cycle', sa.Enum('MONTHLY', 'ANNUAL', name='billing_cycle'), nullable=False),
        sa.Column('status', sa.Enum('TRIALING', 'PENDING', 'ACTIVE', 'PAST_DUE', 'CANCELED', 'EXPIRED', name='subscription_status'), nullable=False),
        sa.Column('gateway', sa.Enum('MOCK', 'PAYHERE', 'STRIPE', name='payment_gateway_name'), nullable=False),
        sa.Column('gateway_subscription_id', sa.String(length=200), nullable=True),
        sa.Column('gateway_customer_id', sa.String(length=200), nullable=True),
        sa.Column('price_lkr', sa.Integer(), nullable=False),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_subscriptions_talent_profile_id', 'subscriptions', ['talent_profile_id'])
    op.create_index('ix_subscriptions_recruiter_profile_id', 'subscriptions', ['recruiter_profile_id'])


def downgrade() -> None:
    op.drop_index('ix_subscriptions_recruiter_profile_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_talent_profile_id', table_name='subscriptions')
    op.drop_table('subscriptions')
    sa.Enum(name='subscription_plan').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='billing_cycle').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='subscription_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='payment_gateway_name').drop(op.get_bind(), checkfirst=True)
