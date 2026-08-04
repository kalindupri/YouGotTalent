"""add talent_lists and talent_list_members tables (recruiter CRM/pipeline lists)

Revision ID: a7b8c0d1e2f3
Revises: f6a7b8c0d1e2
Create Date: 2026-08-02T01:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a7b8c0d1e2f3'
down_revision: Union[str, None] = 'f6a7b8c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'talent_lists',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recruiter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['recruiter_id'], ['recruiter_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_talent_lists_recruiter_id', 'talent_lists', ['recruiter_id'])

    op.create_table(
        'talent_list_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('list_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('talent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['list_id'], ['talent_lists.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['talent_id'], ['talent_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('list_id', 'talent_id', name='uq_talent_list_member_list_talent'),
    )


def downgrade() -> None:
    op.drop_table('talent_list_members')
    op.drop_index('ix_talent_lists_recruiter_id', table_name='talent_lists')
    op.drop_table('talent_lists')
