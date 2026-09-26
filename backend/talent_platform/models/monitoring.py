"""Data minimization models for monitoring sessions, gaze samples, and keystroke dynamics."""

from datetime import datetime
from talent_platform.extensions import db


class Assessment(db.Model):
    """Assessment metadata for proctored evaluation."""
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=60)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    monitoring_sessions = db.relationship(
        "MonitoringSession", back_populates="assessment", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MonitoringSession(db.Model):
    """Proctoring session bound to explicit candidate consent and retention policy."""
    __tablename__ = "monitoring_sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, index=True, nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=True)
    consent_given_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    retention_expires_at = db.Column(db.DateTime, nullable=True)

    candidate = db.relationship("User", backref="monitoring_sessions")
    assessment = db.relationship("Assessment", back_populates="monitoring_sessions")
    gaze_samples = db.relationship(
        "GazeSample", back_populates="session", cascade="all, delete-orphan", lazy="dynamic"
    )
    keystroke_events = db.relationship(
        "KeystrokeEvent", back_populates="session", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "assessment_id": self.assessment_id,
            "consent_given": self.consent_given_at is not None,
            "consent_given_at": self.consent_given_at.isoformat() if self.consent_given_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "retention_expires_at": self.retention_expires_at.isoformat() if self.retention_expires_at else None,
        }


class GazeSample(db.Model):
    """Derived gaze screen landmarks adhering to data minimization (never raw video)."""
    __tablename__ = "gaze_samples"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("monitoring_sessions.id"), nullable=False)
    timestamp_ms = db.Column(db.BigInteger, nullable=False)
    gaze_x = db.Column(db.Float, nullable=False)
    gaze_y = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    off_screen = db.Column(db.Boolean, default=False)

    session = db.relationship("MonitoringSession", back_populates="gaze_samples")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp_ms": self.timestamp_ms,
            "gaze_x": round(self.gaze_x, 4),
            "gaze_y": round(self.gaze_y, 4),
            "confidence": round(self.confidence, 4),
            "off_screen": bool(self.off_screen),
        }


class KeystrokeEvent(db.Model):
    """Derived keystroke timing and categories (never literal keys typed)."""
    __tablename__ = "keystroke_events"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("monitoring_sessions.id"), nullable=False)
    key_category = db.Column(db.String(20), nullable=False)  # 'letter', 'digit', 'backspace', 'space', etc
    dwell_ms = db.Column(db.Integer, nullable=False)
    flight_ms = db.Column(db.Integer, nullable=True)  # gap from previous key

    session = db.relationship("MonitoringSession", back_populates="keystroke_events")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "key_category": self.key_category,
            "dwell_ms": self.dwell_ms,
            "flight_ms": self.flight_ms,
        }
