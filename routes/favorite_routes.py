from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Favorite, Team

favorite_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")

@favorite_bp.get()
@jwt_required()
def list_favorites():
    user_id = int(get_jwt_identity())
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    return jsonify([f.to_dict() for f in favorites]), 200

@favorite_bp.post("/<int:team_id>")
@jwt_required()
def follow_team(team_id):
    user_id = int(get_jwt_identity())

    if not Team.query.get(team_id):
        return jsonify({"error": "Team not found"}), 404

    existing = Favorite.query.filter_by(user_id=user_id, team_id=team_id).first()
    if existing:
        return jsonify({"message":"Already following this team"}), 200

    favorite = Favorite(user_id=user_id, team_id=team_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify(favorite.to_dict()), 201

@favorite_bp.delete("/<int:team_id>")
@jwt_required()
def unfollow_team(team_id):
    user_id = int(get_jwt_identity())
    favorite = Favorite.query.filter_by(user_id=user_id, team_id=team_id).first()
    if not favorite:
        return jsonify({"error": "You are not following this team"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Unfollowed team"}), 200