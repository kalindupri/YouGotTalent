"""allow multiple talent profiles per user

A parent/legal guardian holds one account and may manage a profile for each of their
children, so user_id can no longer be unique. Replaced with a plain index -- every lookup
that used to rely on the unique constraint's implicit index still needs one.

The constraint was declared unnamed in the initial schema (sa.UniqueConstraint('user_id')),
so Postgres auto-named it talent_profiles_user_id_key.

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-08-18T00:00:00

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'f8a9b0c1d2e3'
down_revision: Union[str, None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('talent_profiles_user_id_key', 'talent_profiles', type_='unique')
    op.create_index('ix_talent_profiles_user_id', 'talent_profiles', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_talent_profiles_user_id', table_name='talent_profiles')
    op.create_unique_constraint('talent_profiles_user_id_key', 'talent_profiles', ['user_id'])
