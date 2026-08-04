"""add per-party e-signature fields to bookings, drop agreement_document_url

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-08-04T01:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('bookings', sa.Column('talent_signature_name', sa.String(length=255), nullable=True))
    op.add_column('bookings', sa.Column('talent_signed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('bookings', sa.Column('recruiter_signature_name', sa.String(length=255), nullable=True))
    op.add_column('bookings', sa.Column('recruiter_signed_at', sa.DateTime(timezone=True), nullable=True))
    op.drop_column('bookings', 'agreement_document_url')


def downgrade() -> None:
    op.add_column('bookings', sa.Column('agreement_document_url', sa.String(length=500), nullable=True))
    op.drop_column('bookings', 'recruiter_signed_at')
    op.drop_column('bookings', 'recruiter_signature_name')
    op.drop_column('bookings', 'talent_signed_at')
    op.drop_column('bookings', 'talent_signature_name')
