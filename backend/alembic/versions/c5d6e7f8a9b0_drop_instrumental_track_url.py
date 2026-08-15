"""drop instrumental_track_url from casting_call_roles (mixing feature removed)

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-08-15T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c5d6e7f8a9b0'
down_revision: Union[str, None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('casting_call_roles', 'instrumental_track_url')


def downgrade() -> None:
    op.add_column('casting_call_roles', sa.Column('instrumental_track_url', sa.String(length=500), nullable=True))
