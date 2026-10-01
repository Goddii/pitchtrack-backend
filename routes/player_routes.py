from flask import Blueprint, request, jsonify

from extensions import db
from models import Player, Team
from utils.auth_helpers import admin_required
from utils.player_stats import aggregate_player_stats, player_match_log


player_bp = Blueprint("players", __name__, url_prefix="/api/players")

VALID_POSITIONS = {"Forward", "Midfielder","Defender","Goalkeeper"}
MIN_HEIGHT_CM = 100
MAX_HEIGHT_CM = 230


def _height_error(value):
    """None for a missing or sensible height, otherwise a message for the client."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not MIN_HEIGHT_CM <= value <= MAX_HEIGHT_CM:
        return f"height_cm must be a whole number from {MIN_HEIGHT_CM} to {MAX_HEIGHT_CM}"
    return None


@player_bp.get("")
def list_players():
    team_id = request.args.get("team_id", type=int)
    query = Player.query
    if team_id:
        query = query.filter_by(team_id= team_id)
    players = query.order_by(Player.name.asc()).all()
    return jsonify([p.to_dict() for p in players]), 200

@player_bp.get("/<int:player_id>")
def get_player(player_id):
    player = Player.query.get_or_404(player_id)
    return jsonify(player.to_dict()), 200

@player_bp.get("/<int:player_id>/stats")
def get_player_stats(player_id):
    Player.query.get_or_404(player_id)
    return jsonify(aggregate_player_stats(player_id)), 200

@player_bp.get("/<int:player_id>/matches")
def get_player_matches(player_id):
    player = Player.query.get_or_404(player_id)
    return jsonify(player_match_log(player)), 200

@player_bp.post("")
@admin_required()
def create_player():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    position = data.get("position")
    team_id = data.get("team_id") 

    if not name:
        return jsonify({"error": "Player name is required"}), 400
    if position not in VALID_POSITIONS:
        return jsonify({"error": f"Position must be one of {sorted(VALID_POSITIONS)}"}), 400
    if not team_id or not Team.query.get(team_id):
        return jsonify({"error":"a valid team_id is required"}), 400
    height_error = _height_error(data.get("height_cm"))
    if height_error:
        return jsonify({"error": height_error}), 400

    player = Player(
        name=name,
        position=position,
        team_id=team_id,
        jersey_number= data.get("jersey_number"),
        nationality = data.get("nationality"),
        age=data.get("age"),
        height_cm=data.get("height_cm"),
        photo_url = data.get("photo_url"),
        bio = data.get("bio"),
        attributes = data.get("attributes"),

    )   

    db.session.add(player)
    db.session.commit()
    return jsonify(player.to_dict()), 201


@player_bp.put("/<int:player_id>")
@admin_required()
def update_player(player_id):
    player = Player.query.get_or_404(player_id)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        new_name =(data.get("name") or "").strip()
        if not new_name:
            return jsonify({"error": "Player name cannot be empty"}), 400
        player.name = new_name

    if "position" in data:
        if data["position"] not in VALID_POSITIONS:
            return jsonify({"error": f"Position must be one of {sorted(VALID_POSITIONS)}"}), 400
        player.position = data["position"]

    if "height_cm" in data:
        height_error = _height_error(data["height_cm"])
        if height_error:
            return jsonify({"error": height_error}), 400

    for field in ("jersey_number", "nationality", "age", "height_cm", "photo_url","bio", "attributes"):
        if field in data:
            setattr(player, field, data[field])


    db.session.commit()
    return jsonify(player.to_dict()), 200

@player_bp.delete("/<int:player_id>")
@admin_required()
def delete_player(player_id):
    player = Player.query.get_or_404(player_id)
    # captain_id is a plain id (no foreign key), so clear it here rather than leave it dangling
    Team.query.filter_by(id=player.team_id, captain_id=player.id).update({"captain_id": None})
    db.session.delete(player)
    db.session.commit()
    return jsonify({"message": "Player removed"}), 200              