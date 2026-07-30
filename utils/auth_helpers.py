import re
from functools import wraps

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email):
    return bool(email) and bool(EMAIL_RE.match(email))

def is_valid_password(password):
    "simple baseline at least 6 characters"
    return bool(password) and len(password) >= 6

def admin_required():
    """Route decorator: requires JWT and role =='admin' in its claims"""
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "Admin access required"}), 403
            return fn(*args, **kwargs)

        return decorated
    return wrapper
