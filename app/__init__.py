"""Application factory. Creates and configures the Flask app instance."""
import secrets
from datetime import timedelta
from flask import Flask, jsonify

from app.config import Config
from app.extensions import cache


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # Secret key: use a stable one from env in production. Falling back to a
    # random one is fine for local dev, but sessions won't survive a restart
    # and it breaks multi-worker deployments — set FLASK_SECRET in production.
    app.secret_key = Config.FLASK_SECRET or secrets.token_urlsafe(32)
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        hours=Config.SESSION_LIFETIME_HOURS
    )
    app.config["DEBUG"] = Config.DEBUG

    cache.init_app(app)

    # DB indexes + reference data (roles/statuses) + customer accounts backfill
    from app.db import setup_database, create_accounts_for_customers

    setup_database()
    create_accounts_for_customers()

    from app.routes import register_blueprints

    register_blueprints(app)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"detail": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"detail": "Internal server error"}), 500

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"detail": "Access forbidden"}), 403

    return app
