"""add marketing_posts table (daily draft -> Discord approval -> Facebook post pipeline)

Revision ID: a1b2c3d4e5f6
Revises: f3a4b5c6d7e8
Create Date: 2026-08-09T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    marketing_post_status = postgresql.ENUM(
        'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'POSTED', 'FAILED', 'EXPIRED',
        name='marketing_post_status',
    )
    marketing_post_status.create(op.get_bind(), checkfirst=True)
    # create_type=False on THIS SAME instance — without it, create_table below tries to
    # CREATE TYPE again on its own (the generic sa.Enum(...) has no create_type flag at all;
    # only the postgresql-dialect ENUM does), which fails with DuplicateObject since the
    # explicit .create() call above already made it. See app-guide skill's enum-migration
    # conventions.
    marketing_post_status = postgresql.ENUM(
        'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'POSTED', 'FAILED', 'EXPIRED',
        name='marketing_post_status',
        create_type=False,
    )

    op.create_table(
        'marketing_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', marketing_post_status, nullable=False),
        sa.Column('discord_channel_id', sa.String(length=50), nullable=True),
        sa.Column('discord_message_id', sa.String(length=50), nullable=True),
        sa.Column('facebook_post_id', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('marketing_posts')
    postgresql.ENUM(name='marketing_post_status').drop(op.get_bind(), checkfirst=True)
