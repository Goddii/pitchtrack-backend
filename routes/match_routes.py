from datetime import datetime

from flask import Blueprint, request, jsonify

from extensions import db
from models import Match, Team
from utils.auth_helpers import admin_required


match_bp = Blueprint("matches", __name__, url_prefix="/api/matches")

VALID_STATUSES = {"scheduled", "live", "completed"}

def _parse_date(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None

@match_bp.get("")
def list_matches():
    status = request.args.get("status")
    team_id = request.args.get("team_id", type=int)

    query = Match.query
    if status:
        query = query.filter_by(status=status)
    if team_id:
        query = query.filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        )

    matches = query.order_by(Match.match_date.asc()).all()
    return jsonify([m.to_dict() for m in matches]), 200

    
    