from datetime import datetime
from extensions import db

class Favorite(db.Model):
    __tablename__ = "favorites"
    __tabke_args__ = (
        db.UniqueConstraints("user_id", "team_id", name="uq_user_team_favorite"),

    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id" : self.id,
            "team" : self.team.to_dict() if self.team else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }