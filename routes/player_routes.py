from flask import Blueprint, request, jsonify

from extensions import db
from models import Player, Team
from utils.auth_helpers import admin_required


player_bp = Blueprint("players", __name__, url_prefix="/api/players")

VALID_POSITIONS = {"Forward", "Midfielder","Defender","Goalkeeper"}

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

    player = Player(
        name=name,
        position=position,
        team_id=team_id,
        jersey_number= data.get("jersey_number"),
        nationality = data.get("nationality"),
        age=data.get("age"),
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
        player.team_id = data["team_id"]

    for field in ("jersey_number", "nationality", "age","photo_url","bio", "attributes"):
        if field in data:
            setattr(player, field, data[field])


    db.session.commit()
    return jsonify(player.to_dict()), 200

@player_bp.delete("/<int:player_id>")
@admin_required()
def delete_player(player_id):
    player = Player.query.get_or_404(player_id)
    db.session.delete(player)
    db.session.commit()
    return jsonify({"message": "Player removed"}), 200               