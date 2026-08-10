"""add categories array column to talent_profiles (multi-category talent), backfill from category

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-08-10T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('talent_profiles', sa.Column('categories', sa.ARRAY(sa.String(length=50)), nullable=True))
    op.execute("UPDATE talent_profiles SET categories = ARRAY[category] WHERE categories IS NULL")


def downgrade() -> None:
    op.drop_column('talent_profiles', 'categories')
