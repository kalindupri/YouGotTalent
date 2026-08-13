"""add guide_track_url and instrumental_track_url to casting_call_roles

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-08-14T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, None] = 'a3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('casting_call_roles', sa.Column('guide_track_url', sa.String(length=500), nullable=True))
    op.add_column('casting_call_roles', sa.Column('instrumental_track_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('casting_call_roles', 'instrumental_track_url')
    op.drop_column('casting_call_roles', 'guide_track_url')
