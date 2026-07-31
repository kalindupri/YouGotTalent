"""add pricing_versions table for admin-configurable, versioned subscription pricing

Revision ID: e5f6a7b8c0d1
Revises: d4e5f6a7b8c0
Create Date: 2026-07-31T00:00:00

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'e5f6a7b8c0d1'
down_revision: Union[str, None] = 'd4e5f6a7b8c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create_type=False is only honored by the postgresql-dialect-specific ENUM class (not the
    # generic sa.Enum) — this table reuses the "subscription_plan" type already created by the
    # subscriptions table's migration, so it must NOT try to create it again.
    plan_enum = postgresql.ENUM('TALENT_PREMIUM', 'RECRUITER_PREMIUM', name='subscription_plan', create_type=False)

    op.create_table(
        'pricing_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan', plan_enum, nullable=False),
        sa.Column('monthly_price_lkr', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pricing_versions_plan_created_at', 'pricing_versions', ['plan', 'created_at'])

    # Seed one version per plan matching the app's current hardcoded defaults, so behavior is
    # unchanged immediately after this migration runs — nothing charges differently until an
    # admin actually sets a new price via the admin Pricing page.
    pricing_versions = sa.table(
        'pricing_versions',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('plan', plan_enum),
        sa.column('monthly_price_lkr', sa.Integer()),
    )
    op.bulk_insert(
        pricing_versions,
        [
            {'id': uuid.uuid4(), 'plan': 'TALENT_PREMIUM', 'monthly_price_lkr': 490},
            {'id': uuid.uuid4(), 'plan': 'RECRUITER_PREMIUM', 'monthly_price_lkr': 1500},
        ],
    )


def downgrade() -> None:
    op.drop_index('ix_pricing_versions_plan_created_at', table_name='pricing_versions')
    op.drop_table('pricing_versions')
