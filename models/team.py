from extensions import db

class Team(db.Model):
    __tablename__ = "teams"


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    city = db.Column(db.String(120), nullable=True)
    founded_year = db.Column(db.Integer, nullable=True)
    coach = db.Column(db.String(120), nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)

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
            "logo_url" : self.logo_url
        }
        if include_roster:
            data["player"] = [p.to_dict(include_team=False) for p in self.players]
        return data

    def to_summary(self):
        """lightweight shape for nesting inside match payloads"""
        return{"id":self.id, "name": self.name}

    def __repr__(self):
        return f"<Team {self.name}>"    