import os

from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()

from . import models
from .demo_data import DEMO_DATA


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://talent_app:local_dev_only@localhost:5432/talent_ecosystem",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.get("/")
    @app.get("/dashboard")
    def index():
        return render_template("discovery.html", demo_data=DEMO_DATA)

    @app.get("/login")
    def login():
        return render_template("login.html")

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app
