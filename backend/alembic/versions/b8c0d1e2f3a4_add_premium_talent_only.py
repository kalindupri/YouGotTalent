"""add premium_talent_only column to casting_calls (exclusive talent hunts)

Revision ID: b8c0d1e2f3a4
Revises: a7b8c0d1e2f3
Create Date: 2026-08-02T02:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8c0d1e2f3a4'
down_revision: Union[str, None] = 'a7b8c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'casting_calls',
        sa.Column('premium_talent_only', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('casting_calls', 'premium_talent_only')
