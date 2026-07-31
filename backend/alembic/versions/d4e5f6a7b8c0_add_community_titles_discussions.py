"""add community: titles, reviews, discussions, and report target types

Revision ID: d4e5f6a7b8c0
Revises: c3d4e5f6a7b9
Create Date: 2026-07-31T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd4e5f6a7b8c0'
down_revision: Union[str, None] = 'c3d4e5f6a7b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'titles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('work_type', sa.Enum('FILM', 'TV_SERIES', 'SONG', name='work_type'), nullable=False),
        sa.Column('release_year', sa.Integer(), nullable=True),
        sa.Column('genre', sa.String(length=200), nullable=True),
        sa.Column('language', sa.String(length=50), nullable=True),
        sa.Column('synopsis', sa.Text(), nullable=True),
        sa.Column('poster_url', sa.String(length=500), nullable=True),
        sa.Column('added_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'title_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('titles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('title_id', 'user_id', name='uq_title_review_title_user'),
    )
    op.create_index('ix_title_reviews_title_id', 'title_reviews', ['title_id'])

    op.create_table(
        'discussion_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category', sa.Enum('FILMS', 'TV_SERIES', 'MUSIC', 'INDUSTRY_NEWS', 'GENERAL', name='discussion_category'), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('title_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('titles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('author_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'discussion_replies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('discussion_threads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_discussion_replies_thread_id', 'discussion_replies', ['thread_id'])

    # Postgres allows adding enum values in place — no need to recreate report_target_type.
    for value in ('TITLE', 'TITLE_REVIEW', 'DISCUSSION_THREAD', 'DISCUSSION_REPLY'):
        op.execute(f"ALTER TYPE report_target_type ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Postgres can't drop individual enum values, so the report_target_type additions are left
    # in place on downgrade (harmless — just unused labels) rather than recreating the type.
    op.drop_index('ix_discussion_replies_thread_id', table_name='discussion_replies')
    op.drop_table('discussion_replies')
    op.drop_table('discussion_threads')
    sa.Enum(name='discussion_category').drop(op.get_bind(), checkfirst=True)

    op.drop_index('ix_title_reviews_title_id', table_name='title_reviews')
    op.drop_table('title_reviews')
    op.drop_table('titles')
    sa.Enum(name='work_type').drop(op.get_bind(), checkfirst=True)
