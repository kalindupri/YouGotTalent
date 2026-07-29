"""add casting call roles

Revision ID: f4a2c9b7e1d3
Revises: e31afc91dfcc
Create Date: 2026-07-28 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f4a2c9b7e1d3'
down_revision: Union[str, None] = 'e31afc91dfcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'casting_call_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('casting_call_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('criteria', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('compensation', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['casting_call_id'], ['casting_calls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.add_column('casting_calls', sa.Column('tags', postgresql.ARRAY(sa.String(length=60)), nullable=True))
    op.add_column('casting_calls', sa.Column('shoot_details', sa.String(length=255), nullable=True))

    op.add_column('applications', sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Backfill: give every existing casting call a single default role carrying its old
    # top-level category/compensation, then point existing applications at that role.
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        INSERT INTO casting_call_roles (id, casting_call_id, title, criteria, category, compensation, created_at)
        SELECT gen_random_uuid(), id, title, NULL, category, compensation, created_at
        FROM casting_calls
        """
    ))
    conn.execute(sa.text(
        """
        UPDATE applications a
        SET role_id = r.id
        FROM casting_call_roles r
        WHERE r.casting_call_id = a.casting_call_id
        """
    ))

    op.alter_column('applications', 'role_id', nullable=False)
    op.create_foreign_key(
        'fk_applications_role_id', 'applications', 'casting_call_roles', ['role_id'], ['id'], ondelete='CASCADE'
    )
    op.drop_constraint('uq_application_casting_call_talent', 'applications', type_='unique')
    op.create_unique_constraint('uq_application_role_talent', 'applications', ['role_id', 'talent_id'])


def downgrade() -> None:
    op.drop_constraint('uq_application_role_talent', 'applications', type_='unique')
    op.create_unique_constraint('uq_application_casting_call_talent', 'applications', ['casting_call_id', 'talent_id'])
    op.drop_constraint('fk_applications_role_id', 'applications', type_='foreignkey')
    op.drop_column('applications', 'role_id')
    op.drop_column('casting_calls', 'shoot_details')
    op.drop_column('casting_calls', 'tags')
    op.drop_table('casting_call_roles')
