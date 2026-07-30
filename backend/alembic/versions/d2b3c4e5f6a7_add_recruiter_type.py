"""add recruiter type

Revision ID: d2b3c4e5f6a7
Revises: c1a2b3d4e5f6
Create Date: 2026-07-31T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd2b3c4e5f6a7'
down_revision: Union[str, None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recruiter_profiles', sa.Column('recruiter_type', sa.String(length=20), nullable=False, server_default='agency'))


def downgrade() -> None:
    op.drop_column('recruiter_profiles', 'recruiter_type')
