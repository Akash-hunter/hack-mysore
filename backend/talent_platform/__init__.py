import os

from flask import Flask, abort, redirect, render_template, request, session, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


from .extensions import db, migrate

from . import models
from .demo_data import DEMO_DATA


def create_app(test_config=None):
    import jinja2

    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(base_dir))

    template_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
    )

    # Multi-path template loader to guarantee templates are found in all environments
    search_dirs = [
        template_dir,
        os.path.join(project_root, "templates"),
        os.path.join(os.getcwd(), "templates"),
        os.path.join(os.getcwd(), "backend", "talent_platform", "templates"),
    ]
    valid_dirs = [d for d in search_dirs if os.path.isdir(d)]
    if valid_dirs:
        app.jinja_loader = jinja2.FileSystemLoader(valid_dirs)

    raw_database_url = os.environ.get("DATABASE_URL")
    if not raw_database_url:
        if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            database_url = "sqlite:////tmp/talent_ecosystem.db"
        else:
            try:
                instance_dir = app.instance_path
                os.makedirs(instance_dir, exist_ok=True)
                db_file = os.path.join(instance_dir, "talent_ecosystem.db").replace("\\", "/")
                database_url = f"sqlite:///{db_file}"
            except (OSError, PermissionError):
                database_url = "sqlite:////tmp/talent_ecosystem.db"
    elif raw_database_url.startswith("postgres://"):
        database_url = raw_database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif raw_database_url.startswith("postgresql://") and not raw_database_url.startswith("postgresql+"):
        database_url = raw_database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    else:
        database_url = raw_database_url

    if test_config and test_config.get("TESTING") and "SQLALCHEMY_DATABASE_URI" not in test_config:
        database_url = "sqlite://"

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or "talent-ecosystem-dev-secret-key-change-in-prod",
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        try:
            db.create_all()
        except Exception:
            pass

    from .services.monitoring.routes import monitoring_bp
    app.register_blueprint(monitoring_bp, url_prefix="/api/monitoring")


    @app.get("/")
    def landing():
        return render_template("landing.html")

    @app.get("/login")
    def login():
        return render_template("account.html", mode="login")

    @app.get("/signup")
    def signup():
        return render_template("account.html", mode="signup")

    @app.get("/select-role")
    def select_role():
        flow = request.args.get("flow", "login")
        if flow not in {"login", "signup"}:
            flow = "login"
        current_role = session.get("preview_role")
        if current_role and "flow" not in request.args:
            return redirect(url_for("role_portal", role=current_role))
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

    @app.after_request
    def add_cors_headers(response):
        allowed_origin = os.environ.get("CORS_ALLOWED_ORIGIN", "*")
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    return app
