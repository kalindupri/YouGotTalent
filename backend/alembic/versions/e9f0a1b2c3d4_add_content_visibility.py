"""add visibility column to media, library_items, reels

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-08-12T12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e9f0a1b2c3d4'
down_revision: Union[str, None] = 'd8e9f0a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('media', sa.Column('visibility', sa.String(length=20), nullable=False, server_default='public'))
    op.add_column('library_items', sa.Column('visibility', sa.String(length=20), nullable=False, server_default='public'))
    op.add_column('reels', sa.Column('visibility', sa.String(length=20), nullable=False, server_default='public'))


def downgrade() -> None:
    op.drop_column('reels', 'visibility')
    op.drop_column('library_items', 'visibility')
    op.drop_column('media', 'visibility')
