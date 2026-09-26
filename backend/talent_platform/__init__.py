import os

from flask import Flask, abort, redirect, render_template, request, session, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()

from . import models
from .demo_data import DEMO_DATA


def create_app(test_config=None):
    app = Flask(__name__)

    raw_database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://talent_app:local_dev_only@localhost:5432/talent_ecosystem",
    )
    if raw_database_url.startswith("postgres://"):
        database_url = raw_database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif raw_database_url.startswith("postgresql://") and not raw_database_url.startswith("postgresql+"):
        database_url = raw_database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    else:
        database_url = raw_database_url

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or "talent-ecosystem-dev-secret-key-change-in-prod",
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.get("/")
    def landing():
        return render_template("landing.html")

    @app.get("/login")
    def login():
        if session.get("preview_role"):
            return redirect(url_for("role_portal", role=session["preview_role"]))
        return render_template("account.html", mode="login")

    @app.get("/signup")
    def signup():
        if session.get("preview_role"):
            return redirect(url_for("role_portal", role=session["preview_role"]))
        return render_template("account.html", mode="signup")

    @app.get("/select-role")
    def select_role():
        current_role = session.get("preview_role")
        if current_role:
            return redirect(url_for("role_portal", role=current_role))
        flow = request.args.get("flow", "login")
        if flow not in {"login", "signup"}:
            flow = "login"
        return render_template("select_role.html", flow=flow)

    @app.post("/select-role")
    def set_preview_role():
        role = request.form.get("role")
        if role not in {"student", "recruiter", "institution"}:
            abort(400)
        current_role = session.get("preview_role")
        if current_role:
            if current_role != role:
                abort(403)
            return redirect(url_for("role_portal", role=current_role))
        session["preview_role"] = role
        return redirect(url_for("role_portal", role=role))

    @app.get("/portal/<role>")
    def role_portal(role):
        if role not in {"student", "recruiter", "institution"}:
            abort(404)
        if session.get("preview_role") != role:
            abort(403)
        return render_template(
            "discovery.html", demo_data=DEMO_DATA, initial_role=role
        )

    @app.get("/dashboard")
    def dashboard_preview():
        role = request.args.get("role", "recruiter")
        if role not in {"student", "recruiter", "institution"}:
            abort(404)
        return redirect(url_for("role_portal", role=role))

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("landing"))

    @app.errorhandler(403)
    def forbidden(error):
        return render_template(
            "access_denied.html", preview_role=session.get("preview_role")
        ), 403

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app
