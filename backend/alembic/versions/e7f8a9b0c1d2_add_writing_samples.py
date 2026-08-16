"""add writing_samples table

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-08-16T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, None] = 'd6e7f8a9b0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'writing_samples',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('talent_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('writing_type', sa.String(length=20), nullable=False),
        sa.Column('language', sa.String(length=20), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('visible_lines', sa.Integer(), nullable=False, server_default='8'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default='public'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['talent_profile_id'], ['talent_profiles.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_writing_samples_talent_profile_id', 'writing_samples', ['talent_profile_id'])


def downgrade() -> None:
    op.drop_index('ix_writing_samples_talent_profile_id', table_name='writing_samples')
    op.drop_table('writing_samples')
