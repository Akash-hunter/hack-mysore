import os
import sys

# Ensure VERCEL environment flag is set for serverless read-only filesystem handling
os.environ["VERCEL"] = os.environ.get("VERCEL", "1")

# Add project root and backend to sys.path so talent_platform can be loaded
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from talent_platform import create_app
    app = create_app()
except Exception as e:
    import traceback
    from flask import Flask
    app = Flask(__name__)
    err = traceback.format_exc()

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        return f"<h1>Talent Platform Startup Error on Vercel</h1><pre>{err}</pre>", 500
