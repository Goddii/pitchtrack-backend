from flask import Flask, jsonify

from config import Config
from extensions import db, bcrypt, jwt, migrate, cors

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        resources = {r"/api/*":{"origins":app.config["FRONTEND_ORIGINS"]}},
        supports_credentials = True,
    )

    #models must be imported befor blueprint touch db so migrations see them
    from models import User, Team, Player, Match, Favorite
    from routes.auth_routes import auth_bp
    from routes.team_routes import team_bp
    from routes.player_routes import player_bp
    from routes.match_routes import match_bp
    from routes.favorite_routes import favorite_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(player_bp)
    app.register_blueprint(match_bp)
    app.register_blueprint(favorite_bp)

    # ── AUTO-SEED ON STARTUP (Render free tier — no shell access) ──
    try:
        with app.app_context():
            db.create_all()                     # Ensure tables exist
            if app.config.get("AUTO_SEED", True) and not Team.query.first():  # Only seed if empty
                from seed import seed_database
                seed_database(app)
    except Exception as e:
        app.logger.warning(f"Auto-seed skipped: {e}")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error":"Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "missing or invalid authentication token"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid authentication token"}), 422

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error":"Token has expired"}), 401

    return app