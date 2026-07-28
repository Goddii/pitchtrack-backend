from flask import Blueprint, request, jsonify

from extensions import db
from models import Team
from utils.auth_helpers import admin_required

team_bp = Blueprint("teams", __name__, url_prefix="/api/teams")

@team_bp.get("")
def list_teams():
    teams = Team.query.order_by(Team.name.asc()).all()
    return jsonify([t.to.dict() for t in teams]), 200

@team_bp.get("/<int:team_id>")
def get_team(team_id):
    team = Team.query.get_or_404(team_id)
    return jsonify(team.to_dict(include_roster=True)), 200


@team_bp.post("")
@admin_required()
def create_team():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "Team name is required"}), 400

    if Team.query.filter_by(name=name).first():
        return jsonify({"error":"a team with that name already exists"}), 409

    team = Team(
        name= name,
        city = data.get("city"),
        founded_year = data.get("founded_year"),
        coach = data.get("coach"),
        logo_url = data.get("logo_url"),
    )
    db.session.add(team)
    db.session.commit()
    return jsonify(team.to_dict()), 201

@team_bp.put("/<int:team_id>")
@admin_required()
def update_team(team_id):
    team = Team.query.get_or_404(team_id)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        new_name = (data.get("name") or "").strip()
        if not new_name:
            return jsonify({"error": "Team name cannot be empty"}), 400
        existing = Team.query.filter_by(name=new_name).first()
        if existing and existing.id != team.id:
            return jsonify({"error": "A team with that name already exists"}), 409
        team.name = new_name

    for field in ("city", "founded_year", "coach", "logo_url"):
        if field in data:
            setattr(team, field, data[field])

    db.session.commit()
    return jsonify(team.to_dict()),200


@team_bp.delete("/<int:team_id>")
@admin_required()
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)
    db.session.delete(team)
    db.session.commit()
    return jsonify({"message": "Team deleted"}), 200