"""add application read receipts (viewed_at) and profile_views table

Revision ID: f6a7b8c0d1e2
Revises: e5f6a7b8c0d1
Create Date: 2026-08-02T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f6a7b8c0d1e2'
down_revision: Union[str, None] = 'e5f6a7b8c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('applications', sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        'profile_views',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('talent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recruiter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('viewed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['talent_id'], ['talent_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recruiter_id'], ['recruiter_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_profile_views_talent_id', 'profile_views', ['talent_id'])


def downgrade() -> None:
    op.drop_index('ix_profile_views_talent_id', table_name='profile_views')
    op.drop_table('profile_views')
    op.drop_column('applications', 'viewed_at')
