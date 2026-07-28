"""Registers every blueprint onto the Flask app."""


def register_blueprints(app):
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.transaction_routes import transaction_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transaction_bp)
