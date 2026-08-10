"""make booking start_at/end_at nullable, add contract_content (offer/contract flow)

Revision ID: c7d8e9f0a1b2
Revises: f6a7b8c9d0e1
Create Date: 2026-08-10T07:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('bookings', 'start_at', existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column('bookings', 'end_at', existing_type=sa.DateTime(timezone=True), nullable=True)
    op.add_column('bookings', sa.Column('contract_content', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('bookings', 'contract_content')
    op.alter_column('bookings', 'end_at', existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column('bookings', 'start_at', existing_type=sa.DateTime(timezone=True), nullable=False)
