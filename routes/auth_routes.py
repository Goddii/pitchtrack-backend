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

    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if not is_valid_email(email):
        return jsonify({'error':'A valid email is required'}), 400
    if not is_valid_password(password):
        return jsonify({'error':'Password must be at least 6 characters'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with that email already exists'}), 409


    user = User(name=name, email=email, role="user")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(
        identity = str(user.id), additional_claims={"role": user.role}
    )
    return jsonify({"token": token, "user": user.to_dict()}), 201

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error":"Invalid email or password"}), 401

    token = create_access_token(
        identity=str(user.id), additional_claims={"role":user.role}

    )
    return jsonify({'token': token, 'user': user.to_dict()}), 200