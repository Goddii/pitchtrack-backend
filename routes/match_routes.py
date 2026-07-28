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

@match_bp.post("")
@admin_required()
def create_match():
    data = request.get_json(silent=True) or {}
    home_team_id = data.get("home_team_id")
    away_team_id = data.get("away_team_id")
    match_date = _parse_date(data.get("match_date"))


    if not home_team_id or not away_team_id:
        return jsonify({"error": "home_team_id and away_team_id are required"}), 400
    if home_team_id == away_team_id:
        return jsonify({"error": "A team cannot play itself"}), 400
    if not Team.query.get(home_team_id) or not Team.query.get(away_team_id):
        return jsonify({"error":"Both teams must exist"}), 400
    if not match_date:
        return jsonify({"error": "match_date is requires in ISO format"}), 400

    status = data.get("status", "scheduled")
    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400


    match = Match(
        home_team_id = home_team_id,
        away_team_id = away_team_id,
        match_date = match_date,
        venue = data.get("venue"),
        status = status,
        home_score = data.get("home_score"),
        away_score = data.get("away_score"),
        minute = data.get("minute"),
    )
    db.session.add(match)
    db.session.commit()
    return jsonify(match.to_dict()), 201



    