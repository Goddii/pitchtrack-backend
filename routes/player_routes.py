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