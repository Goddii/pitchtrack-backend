from extensions import db

class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    match_date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="scheduled")
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    minute = db.Column(db.Integer, nullable=True) #elapsed minute relevanr while status == live


    def to_dict(self):
        return {
            "id": self.id,
            "home_team" : self.home_team.to_summary() if self.home_team else None,
            "away_team": self.away_team.to_summary() if self.away_team else None,
            "match_date": self.match_date.isoformat() if self.match_date else None,
            "venue" : self.venue,
            "status" : self.status,
            "home_score" : self.home_score,
            "away_score" : self.away_score,
            "minute" : self.minute,
        }

    def __repr__(self):
        return f"<Match {self.home_team_id} vs {self.away_team_id}>"