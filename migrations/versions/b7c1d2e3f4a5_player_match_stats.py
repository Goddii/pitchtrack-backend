"""player match stats and player height

Adds the per-match player stats table and players.height_cm.

Written to be re-runnable: the app also calls db.create_all() on startup, which creates new
tables (but never new columns), so either object may already exist when this runs.

Revision ID: b7c1d2e3f4a5
Revises: ace0ba1ec2fe
Create Date: 2026-10-01 12:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c1d2e3f4a5'
down_revision = 'ace0ba1ec2fe'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())

    if 'player_match_stats' not in inspector.get_table_names():
        op.create_table('player_match_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('started', sa.Boolean(), nullable=False),
        sa.Column('minutes_played', sa.Integer(), nullable=False),
        sa.Column('goals', sa.Integer(), nullable=False),
        sa.Column('assists', sa.Integer(), nullable=False),
        sa.Column('yellow_cards', sa.Integer(), nullable=False),
        sa.Column('red_cards', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'match_id', name='uq_player_match_stat')
        )

    player_columns = {column['name'] for column in inspector.get_columns('players')}
    if 'height_cm' not in player_columns:
        with op.batch_alter_table('players', schema=None) as batch_op:
            batch_op.add_column(sa.Column('height_cm', sa.Integer(), nullable=True))


def downgrade():
    inspector = sa.inspect(op.get_bind())

    player_columns = {column['name'] for column in inspector.get_columns('players')}
    if 'height_cm' in player_columns:
        with op.batch_alter_table('players', schema=None) as batch_op:
            batch_op.drop_column('height_cm')

    if 'player_match_stats' in inspector.get_table_names():
        op.drop_table('player_match_stats')
