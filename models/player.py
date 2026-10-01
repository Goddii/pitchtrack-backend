from extensions import db

class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(50), nullable=False) #forward | midfielder | defender | goalkeeper
    jersey_number = db.Column(db.Integer, nullable=True)
    nationality = db.Column(db.String(80), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    attributes = db.Column(db.JSON, nullable=True) #eg shooting
    height_cm = db.Column(db.Integer, nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)


    def to_dict(self, include_team=True):
        data = {
            "id": self.id,
            "name" : self.name,
            "position" : self.position,
            "jersey_number" : self.jersey_number,
            "nationality" : self.nationality,
            "age" : self.age,
            "height_cm" : self.height_cm,
            "photo_url" : self.photo_url,
            "bio" : self.bio,
            "attributes" : self.attributes,
        }

        if include_team:
            data["team"] = self.team.to_summary() if self.team else None
        else:
            data["team_id"] = self.team_id
        return data

    def __repr__(self):
        return f"<Player {self.name}>"        