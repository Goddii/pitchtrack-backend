from datetime import datetime

from flask import Blueprint, request, jsonify

from extensions import db
from models import Match, PlayerMatchStat, Team
from utils.auth_helpers import admin_required
from utils.formations import parse_formation
from utils.player_stats import parse_stat_row, validate_match_stats


match_bp = Blueprint("matches", __name__, url_prefix="/api/matches")

VALID_STATUSES = {"scheduled", "live", "completed"}
FORMATION_FIELDS = ("home_formation", "away_formation")

def _parse_date(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None

@match_bp.get("/<int:match_id>")
def get_match(match_id):
    match = Match.query.get_or_404(match_id)
    return jsonify(match.to_dict()), 200

def _stats_payload(match_id):
    stats = PlayerMatchStat.query.filter_by(match_id=match_id).all()
    stats.sort(key=lambda s: (s.player.team_id, s.player.jersey_number or 0))
    return [s.to_dict() for s in stats]

@match_bp.get("/<int:match_id>/player-stats")
def list_match_player_stats(match_id):
    Match.query.get_or_404(match_id)
    return jsonify(_stats_payload(match_id)), 200

@match_bp.put("/<int:match_id>/player-stats")
@admin_required()
def save_match_player_stats(match_id):
    """Create or update player rows for a match. The whole batch is validated before anything is saved."""
    match = Match.query.get_or_404(match_id)
    raw_rows = (request.get_json(silent=True) or {}).get("stats")
    if not isinstance(raw_rows, list) or not raw_rows:
        return jsonify({"error": "stats must be a non-empty list"}), 400

    rows, seen = [], set()
    for raw in raw_rows:
        row, error = parse_stat_row(raw)
        if error:
            return jsonify({"error": error}), 400
        if row["player_id"] in seen:
            return jsonify({"error": f"Player {row['player_id']} appears more than once"}), 400
        seen.add(row["player_id"])
        rows.append(row)

    error = validate_match_stats(match, rows)
    if error:
        return jsonify({"error": error}), 400

    existing = {s.player_id: s for s in PlayerMatchStat.query.filter_by(match_id=match.id)}
    for row in rows:
        stat = existing.get(row["player_id"]) or PlayerMatchStat(match_id=match.id)
        for field, value in row.items():
            setattr(stat, field, value)
        db.session.add(stat)
    db.session.commit()
    return jsonify(_stats_payload(match.id)), 200

@match_bp.delete("/<int:match_id>/player-stats/<int:player_id>")
@admin_required()
def delete_match_player_stat(match_id, player_id):
    stat = PlayerMatchStat.query.filter_by(match_id=match_id, player_id=player_id).first_or_404()
    db.session.delete(stat)
    db.session.commit()
    return jsonify({"message": "Stat removed"}), 200

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

    formations = {}
    for field in FORMATION_FIELDS:
        if field in data:
            clean, error = parse_formation(data[field])
            if error:
                return jsonify({"error": f"{field}: {error}"}), 400
            formations[field] = clean

    for field in ("venue", "home_score", "away_score", "minute"):
        if field in data:
            setattr(match, field, data[field])
    for field, clean in formations.items():
        setattr(match, field, clean)

    db.session.commit()
    return jsonify(match.to_dict()), 200

@match_bp.delete("/<int:match_id>")
@admin_required()
def delete_match(match_id):
    match = Match.query.get_or_404(match_id)
    db.session.delete(match)
    db.session.commit()
    return jsonify({"message":"Match deleted"}), 200






    