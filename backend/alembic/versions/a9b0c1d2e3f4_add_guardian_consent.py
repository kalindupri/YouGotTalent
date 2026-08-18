"""add guardian consent

Guardian consent for under-18 talent, per the PDPA's treatment of a child's personal data as a
special category requiring the consent of a parent or legal guardian.

All statuses are String(20) rather than native Postgres enums, matching talent_profiles.tier
and media.media_type -- so a future status needs no ALTER TYPE.

Revision ID: a9b0c1d2e3f4
Revises: f8a9b0c1d2e3
Create Date: 2026-08-18T00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a9b0c1d2e3f4'
down_revision: Union[str, None] = 'f8a9b0c1d2e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'guardian_consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('talent_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('guardian_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('guardian_full_name', sa.String(length=255), nullable=False),
        sa.Column('guardian_relationship', sa.String(length=40), nullable=False),
        sa.Column('guardian_email', sa.String(length=255), nullable=True),
        sa.Column('guardian_phone', sa.String(length=32), nullable=True),
        sa.Column('minor_full_name', sa.String(length=255), nullable=False),
        sa.Column('minor_date_of_birth', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='required'),
        sa.Column('consented_scopes', postgresql.ARRAY(sa.String(length=40)), nullable=True),
        sa.Column('terms_version', sa.String(length=20), nullable=True),
        sa.Column('privacy_version', sa.String(length=20), nullable=True),
        sa.Column('consent_statement', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['talent_profile_id'], ['talent_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['guardian_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id']),
    )
    op.create_index('ix_guardian_consents_talent_profile_id', 'guardian_consents', ['talent_profile_id'])
    op.create_index('ix_guardian_consents_status', 'guardian_consents', ['status'])

    op.create_table(
        'guardian_consent_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('guardian_consent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doc_type', sa.String(length=30), nullable=False),
        # A storage key, never a URL: these live in the private container and are only
        # readable through the admin-only signed-link route.
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('sha256', sa.String(length=64), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['guardian_consent_id'], ['guardian_consents.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_guardian_consent_documents_consent_id', 'guardian_consent_documents', ['guardian_consent_id'])

    op.create_table(
        'guardian_consent_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('guardian_consent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_status', sa.String(length=20), nullable=True),
        sa.Column('to_status', sa.String(length=20), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['guardian_consent_id'], ['guardian_consents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id']),
    )
    op.create_index('ix_guardian_consent_events_consent_id', 'guardian_consent_events', ['guardian_consent_id'])

    op.add_column(
        'talent_profiles',
        sa.Column('guardian_consent_status', sa.String(length=20), nullable=False, server_default='not_required'),
    )
    # Both the age search filters and the new "is this talent listable" filter range-scan
    # date_of_birth, and there was no index on it.
    op.create_index('ix_talent_profiles_date_of_birth', 'talent_profiles', ['date_of_birth'])


def downgrade() -> None:
    op.drop_index('ix_talent_profiles_date_of_birth', table_name='talent_profiles')
    op.drop_column('talent_profiles', 'guardian_consent_status')
    op.drop_index('ix_guardian_consent_events_consent_id', table_name='guardian_consent_events')
    op.drop_table('guardian_consent_events')
    op.drop_index('ix_guardian_consent_documents_consent_id', table_name='guardian_consent_documents')
    op.drop_table('guardian_consent_documents')
    op.drop_index('ix_guardian_consents_status', table_name='guardian_consents')
    op.drop_index('ix_guardian_consents_talent_profile_id', table_name='guardian_consents')
    op.drop_table('guardian_consents')
