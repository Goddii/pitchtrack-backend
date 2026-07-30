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

@match_bp.get("/<int:match_id>")
def get_match(match_id):
    match = Match.query.get_or_404(match_id)
    return jsonify(match.to_dict()), 200

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


@match_bp.put("/<int:match_id>")
@admin_required()
def update_match(match_id):
    match = Match.query.get_or_404(match_id)
    data = request.get_json(silent=True) or {}

    if "home_team_id" in data:
        if not Team.query.get(data["home_team_id"]):
            return jsonify({"error":"a valid home_team_id is required"}), 400
        match.home_team_id = data["home_team_id"]

    if "away_team_id" in data:
        if not Team.query.get(data["away_team_id"]):
            return jsonify({"error": "A valid away_team_id is required"}), 400
        match.away_team_id = data["away_team_id"]

    if match.home_team_id == match.away_team_id:
        return jsonify({"error": "A team cannot play itself"}), 400

    if "match_date" in data:
        parsed = _parse_date(data["match_date"])
        if not parsed:
            return jsonify({"error": "match_date must be in ISO format"}), 400
        match.match_date = parsed

    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400
        match.status = data["status"]

    for field in ("venue", "home_score", "away_score", "minute"):
        if field in data:
            setattr(match, field, data[field])

    db.session.commit()
    return jsonify(match.to_dict()), 200

@match_bp.delete("/<int:match_id>")
@admin_required()
def delete_match(match_id):
    match = Match.query.get_or_404(match_id)
    db.session.delete(match)
    db.session.commit()
    return jsonify({"message":"Match deleted"}), 200






    