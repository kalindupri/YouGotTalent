"""add awaiting_topic status to marketing_posts, make topic/content nullable

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-09T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres 12+ allows adding an enum value inside a transaction as long as it isn't used
    # in that same transaction — nothing below reads/writes the new value, so this is safe.
    # Uppercase to match the existing labels — SQLAlchemy's Enum(MarketingPostStatus) stores
    # the Python enum member's .name (e.g. "PENDING_APPROVAL"), not its lowercase .value.
    op.execute("ALTER TYPE marketing_post_status ADD VALUE IF NOT EXISTS 'AWAITING_TOPIC'")
    op.alter_column('marketing_posts', 'topic', existing_type=sa.String(length=200), nullable=True)
    op.alter_column('marketing_posts', 'content', existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE — leaving the enum value in place on downgrade
    # is the standard tradeoff here (harmless if unused).
    op.alter_column('marketing_posts', 'content', existing_type=sa.Text(), nullable=False)
    op.alter_column('marketing_posts', 'topic', existing_type=sa.String(length=200), nullable=False)
