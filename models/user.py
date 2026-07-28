import secrets
from datetime import datetime, timedelta
from extensions import db, bcrypt


class User(db.Model):
    __tablename__ = "users"


    id = db.Column(db.integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user") #user /admin

    reset_token = db.Column(db.String(64), nullable=True, index=True)
    reset_token_expires_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default= datetime.utcnow)
    updated_at = db.Column(db.DateTime, default= datetime.utcnow, onupdate=datetime.utcnow)

    favorites = db.relationship(
        "Favorite", backref="user", cascade="all, delete-orphan" lazy=True
    )

    #password helpers
    def set_password(self, raw_password):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    #password reset helpers
    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires_at = datetime.utcnow() + timedelta(minutes=30)
        return self.reset_token

    def reset_token_is_valid(self, token):
        return (
            self.reset_token is not None
            and self.reset_token == token
            and self.reset_token_expires_at is not None
            and self.reset_token_expires_at > datetime.utcnow()
        )

    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expires_at = None


    # serialization
    @property
    def is_admin(self):
        return self.role == "admin"

    def to_dict(self):
        return{
            "id" : self.id,
            "name": self.name,
            "email" : self.email,
            "role" : self.role,
            "created_at" : self.created_at.isoformat() if self.created_at else None,
        }        

    def __repr__(self):
        return f"<User {self.email}>"