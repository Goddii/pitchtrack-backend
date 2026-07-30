from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from extensions import db
from models import User
from utils.auth_helpers import is_valid_email, is_valid_password
from utils.email_helpers import send_password_reset_email


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

@auth_bp.post("/forgot-password")
def forgot_password():
    """
    Issues a password reset token and emails it to the user via Resend.
    Always returns the same generic message — never reveals whether
    the email exists or whether delivery succeeded.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    user = User.query.filter_by(email=email).first()

    if user:
        token = user.generate_reset_token()
        db.session.commit()

        frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
        reset_url = f"{frontend_url}/reset-password?token={token}&email={email}"

        # Send the email; log failures server-side but never tell the client.
        send_password_reset_email(email, reset_url)

    # Always return the same generic message regardless of outcome.
    return jsonify(
        {"message": "If an account with that email exists, a reset link has been generated"}
    ), 200

@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    token = data.get("token") or ""
    new_password = data.get("new_password") or ""

    if not is_valid_password(new_password):
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.reset_token_is_valid(token):
        return jsonify({"error": "Invalid or expired reset token"}), 400

    user.set_password(new_password)
    user.clear_reset_token()
    db.session.commit()

    return jsonify({"message": "Password has been reset.You can now login in"}), 200

@auth_bp.get("/me")
@jwt_required()
def get_me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    return jsonify(user.to_dict()), 200

@auth_bp.put("/me")
@jwt_required()
def update_me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error":"Name cannot be empty"}), 400
        user.name = name

    if "email" in data:
        new_email = (data.get("email") or "").strip().lower()
        if not is_valid_email(new_email):
            return jsonify({"error": "A valid email is required"}), 400
        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != user.id:
            return jsonify({"error": "That email is already in use"}), 409
        user.email = new_email

    if "password" in data and data.get("password"):
        if not is_valid_password(data["password"]):
            return jsonify({"error": "Password must be atleast 6 characters" }), 400
        user.set_password(data['password'])

    user.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify(user.to_dict()), 200

@auth_bp.post("/logout")
@jwt_required()
def logout():
    # jwt are stateless here so "logging out" is really just the client
    # discarding its token This endpoint exists for a consistent api contract
    # and a place to hook in a token blocklist later if needed
    return jsonify({"message": "Logged out successfully"}), 200
