"""add support_conversations and support_messages tables

Revision ID: a3b4c5d6e7f8
Revises: e9f0a1b2c3d4
Create Date: 2026-08-13T02:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, None] = 'e9f0a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'support_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('guest_label', sa.String(length=100), nullable=True),
        sa.Column('discord_thread_id', sa.String(length=32), nullable=False),
        sa.Column('last_seen_discord_message_id', sa.String(length=32), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        'support_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('support_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_support_messages_conversation_id', 'support_messages', ['conversation_id'])


def downgrade() -> None:
    op.drop_index('ix_support_messages_conversation_id', table_name='support_messages')
    op.drop_table('support_messages')
    op.drop_table('support_conversations')
