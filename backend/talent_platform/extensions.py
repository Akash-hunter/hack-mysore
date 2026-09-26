"""Flask extensions for talent_platform."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

__all__ = ["db", "migrate"]
