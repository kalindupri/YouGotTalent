"""add gender and tiktok_followers to talent_profiles (for smarter search filtering)

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-08-15T03:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd6e7f8a9b0c1'
down_revision: Union[str, None] = 'c5d6e7f8a9b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('talent_profiles', sa.Column('gender', sa.String(length=20), nullable=True))
    op.add_column('talent_profiles', sa.Column('tiktok_followers', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('talent_profiles', 'tiktok_followers')
    op.drop_column('talent_profiles', 'gender')
