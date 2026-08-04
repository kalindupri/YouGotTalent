"""add instruments column to talent_profiles (structured multi-select instrument filtering)

Revision ID: c0d1e2f3a4b5
Revises: b8c0d1e2f3a4
Create Date: 2026-08-02T03:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c0d1e2f3a4b5'
down_revision: Union[str, None] = 'b8c0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('talent_profiles', sa.Column('instruments', sa.ARRAY(sa.String(length=60)), nullable=True))


def downgrade() -> None:
    op.drop_column('talent_profiles', 'instruments')
