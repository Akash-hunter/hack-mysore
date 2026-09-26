import os
from flask import Flask
from .extensions import db, migrate
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Create tables if not using migrations for initial setup (optional, here we rely on migrations)
    with app.app_context():
        # Import models here to ensure they are registered with SQLAlchemy
        from .models import user, organization
        # db.create_all()

    return app