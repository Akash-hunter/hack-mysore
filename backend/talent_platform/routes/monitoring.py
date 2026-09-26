"""Re-export monitoring blueprint from services for convenient route imports."""

from ..services.monitoring.routes import monitoring_bp

__all__ = ["monitoring_bp"]
