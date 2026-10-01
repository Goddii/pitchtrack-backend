from extensions import db


class PlayerMatchStat(db.Model):
    """One player's numbers for one match. A row with minutes_played == 0 is an unused substitute."""

    __tablename__ = "player_match_stats"
    __table_args__ = (
        db.UniqueConstraint("player_id", "match_id", name="uq_player_match_stat"),
    )

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    started = db.Column(db.Boolean, nullable=False, default=False)
    minutes_played = db.Column(db.Integer, nullable=False, default=0)
    goals = db.Column(db.Integer, nullable=False, default=0)
    assists = db.Column(db.Integer, nullable=False, default=0)
    yellow_cards = db.Column(db.Integer, nullable=False, default=0)
    red_cards = db.Column(db.Integer, nullable=False, default=0)
    # How the goals were scored. Together they may be fewer than `goals` (unclassified), never more.
    penalty_goals = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    headed_goals = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    right_foot_goals = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    left_foot_goals = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    player = db.relationship(
        "Player",
        backref=db.backref("match_stats", cascade="all, delete-orphan", lazy=True),
    )
    match = db.relationship(
        "Match",
        backref=db.backref("player_stats", cascade="all, delete-orphan", lazy=True),
    )

    def to_dict(self):
        return {
            "match_id": self.match_id,
            "player": {
                "id": self.player.id,
                "name": self.player.name,
                "position": self.player.position,
                "jersey_number": self.player.jersey_number,
                "team_id": self.player.team_id,
            },
            "started": self.started,
            "minutes_played": self.minutes_played,
            "goals": self.goals,
            "assists": self.assists,
            "yellow_cards": self.yellow_cards,
            "red_cards": self.red_cards,
            "penalty_goals": self.penalty_goals,
            "headed_goals": self.headed_goals,
            "right_foot_goals": self.right_foot_goals,
            "left_foot_goals": self.left_foot_goals,
        }

    def __repr__(self):
        return f"<PlayerMatchStat player={self.player_id} match={self.match_id}>"
