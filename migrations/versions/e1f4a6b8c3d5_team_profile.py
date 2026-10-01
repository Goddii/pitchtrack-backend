"""team profile fields

Adds the optional club profile shown on the team page: nickname, stadium, capacity and the captain's
player id. All are NULL until an admin fills them in. The captain is a plain id with no foreign key
(teams and players already point at each other); the API checks and clears it.

Re-runnable: columns that already exist are skipped.

Revision ID: e1f4a6b8c3d5
Revises: d9e3f5a7b2c4
Create Date: 2026-10-01 20:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1f4a6b8c3d5'
down_revision = 'd9e3f5a7b2c4'
branch_labels = None
depends_on = None

PROFILE_COLUMNS = (
    ('nickname', sa.String(length=120)),
    ('stadium', sa.String(length=120)),
    ('capacity', sa.Integer()),
    ('captain_id', sa.Integer()),
)


def _existing_columns():
    return {column['name'] for column in sa.inspect(op.get_bind()).get_columns('teams')}


def upgrade():
    existing = _existing_columns()
    missing = [(name, kind) for name, kind in PROFILE_COLUMNS if name not in existing]
    if not missing:
        return

    with op.batch_alter_table('teams', schema=None) as batch_op:
        for name, kind in missing:
            batch_op.add_column(sa.Column(name, kind, nullable=True))


def downgrade():
    existing = _existing_columns()
    present = [name for name, _ in PROFILE_COLUMNS if name in existing]
    if not present:
        return

    with op.batch_alter_table('teams', schema=None) as batch_op:
        for name in present:
            batch_op.drop_column(name)
