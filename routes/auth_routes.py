from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from extensions import db
from models import User
from utils.auth_helpers import is_valid_email, is_valid_password


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or " ").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""