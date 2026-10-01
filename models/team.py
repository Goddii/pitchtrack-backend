from extensions import db

class Team(db.Model):
    __tablename__ = "teams"


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    city = db.Column(db.String(120), nullable=True)
    founded_year = db.Column(db.Integer, nullable=True)
    coach = db.Column(db.String(120), nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    nickname = db.Column(db.String(120), nullable=True)
    stadium = db.Column(db.String(120), nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    # A plain id, not a foreign key: teams and players already point at each other, so the routes
    # check the player belongs to the team and clear this when that player is deleted.
    captain_id = db.Column(db.Integer, nullable=True)

    players = db.relationship(
        "Player", backref="team", cascade="all, delete-orphan", lazy=True
    )
    home_matches = db.relationship(
        "Match",
        foreign_keys = "Match.home_team_id",
        backref = "home_team",
        cascade="all, delete-orphan",
        lazy=True,
    )
    away_matches = db.relationship(
    "Match", foreign_keys="Match.away_team_id",
    backref="away_team", cascade="all, delete-orphan", lazy=True,
    )

    favorited_by = db.relationship(
        "Favorite", backref="team", cascade="all, delete-orphan", lazy=True
    )

    def to_dict(self, include_roster=False):
        data = {
            "id" : self.id,
            "name" : self.name,
            "city" : self.city,
            "founded_year" : self.founded_year,
            "coach" : self.coach,
            "logo_url" : self.logo_url,
            "nickname": self.nickname,
            "stadium": self.stadium,
            "capacity": self.capacity,
            "captain_id": self.captain_id,
        }
        if include_roster:
            data["players"] = [p.to_dict(include_team=False) for p in self.players]
        return data

    def to_summary(self):
        """lightweight shape for nesting inside match payloads"""
        return{"id":self.id, "name": self.name}

    def __repr__(self):
        return f"<Team {self.name}>"    