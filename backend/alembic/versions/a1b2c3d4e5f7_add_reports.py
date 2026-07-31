"""add reports

Revision ID: a1b2c3d4e5f7
Revises: d2b3c4e5f6a7
Create Date: 2026-07-31T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'd2b3c4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('reporter_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.Enum('BUG', 'SPAM', 'HARASSMENT', 'FAKE_PROFILE', 'INAPPROPRIATE_CONTENT', 'OTHER', name='report_category'), nullable=False),
        sa.Column('target_type', sa.Enum('TALENT_PROFILE', 'RECRUITER_PROFILE', 'CASTING_CALL', 'MESSAGE', name='report_target_type'), nullable=True),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('page_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.Enum('OPEN', 'IN_REVIEW', 'RESOLVED', 'DISMISSED', name='report_status'), nullable=False, server_default='OPEN'),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_reports_status', 'reports', ['status'])


def downgrade() -> None:
    op.drop_index('ix_reports_status', table_name='reports')
    op.drop_table('reports')
    sa.Enum(name='report_category').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='report_target_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='report_status').drop(op.get_bind(), checkfirst=True)
