"""match formations

Adds optional home and away formation text (for example "4-3-3") to matches. Both are NULL until an
admin sets them, in which case the lineup page works the formation out from the starters.

Re-runnable: columns that already exist are skipped.

Revision ID: d9e3f5a7b2c4
Revises: c8d2e4f6a1b3
Create Date: 2026-10-01 17:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9e3f5a7b2c4'
down_revision = 'c8d2e4f6a1b3'
branch_labels = None
depends_on = None

FORMATION_COLUMNS = ('home_formation', 'away_formation')


def _existing_columns():
    return {column['name'] for column in sa.inspect(op.get_bind()).get_columns('matches')}


def upgrade():
    missing = [name for name in FORMATION_COLUMNS if name not in _existing_columns()]
    if not missing:
        return

    with op.batch_alter_table('matches', schema=None) as batch_op:
        for name in missing:
            batch_op.add_column(sa.Column(name, sa.String(length=10), nullable=True))


def downgrade():
    present = [name for name in FORMATION_COLUMNS if name in _existing_columns()]
    if not present:
        return

    with op.batch_alter_table('matches', schema=None) as batch_op:
        for name in present:
            batch_op.drop_column(name)
