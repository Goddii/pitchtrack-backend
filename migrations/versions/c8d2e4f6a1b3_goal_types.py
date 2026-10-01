"""goal types on player match stats

Adds penalty, header, right foot and left foot goal counters to player_match_stats.
They default to 0 on the server side so existing rows and older code stay valid.

Re-runnable: columns that already exist are skipped.

Revision ID: c8d2e4f6a1b3
Revises: b7c1d2e3f4a5
Create Date: 2026-10-01 13:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8d2e4f6a1b3'
down_revision = 'b7c1d2e3f4a5'
branch_labels = None
depends_on = None

GOAL_TYPE_COLUMNS = ('penalty_goals', 'headed_goals', 'right_foot_goals', 'left_foot_goals')


def _existing_columns():
    return {column['name'] for column in sa.inspect(op.get_bind()).get_columns('player_match_stats')}


def upgrade():
    missing = [name for name in GOAL_TYPE_COLUMNS if name not in _existing_columns()]
    if not missing:
        return

    with op.batch_alter_table('player_match_stats', schema=None) as batch_op:
        for name in missing:
            batch_op.add_column(sa.Column(name, sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    present = [name for name in GOAL_TYPE_COLUMNS if name in _existing_columns()]
    if not present:
        return

    with op.batch_alter_table('player_match_stats', schema=None) as batch_op:
        for name in present:
            batch_op.drop_column(name)
