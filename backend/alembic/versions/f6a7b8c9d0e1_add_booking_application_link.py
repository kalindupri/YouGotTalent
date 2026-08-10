"""add application_id link to bookings (offer/contract flow)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-10T01:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bookings',
        sa.Column(
            'application_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('applications.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )
    op.create_index('ix_bookings_application_id', 'bookings', ['application_id'])


def downgrade() -> None:
    op.drop_index('ix_bookings_application_id', table_name='bookings')
    op.drop_column('bookings', 'application_id')
