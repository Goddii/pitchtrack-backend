from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Favorite, Team


favorite_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")

@favorite_bp.get("")
@jwt_required()
def l