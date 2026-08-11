"""add reels table (premium talent Reels showcase)

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-08-12T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd8e9f0a1b2c3'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('talent_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('talent_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('caption', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_reels_talent_profile_id', 'reels', ['talent_profile_id'])


def downgrade() -> None:
    op.drop_index('ix_reels_talent_profile_id', table_name='reels')
    op.drop_table('reels')
