"""Benchmark dataset, data minimization utilities, and retention cleanup for monitoring."""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional
from talent_platform.extensions import db
from talent_platform.models.monitoring import (
    Assessment,
    GazeSample,
    KeystrokeEvent,
    MonitoringSession,
)
from talent_platform.models import User

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Data Minimization: Key Categorization
# -----------------------------------------------------------------------------

def categorize_key(key: Optional[str]) -> str:
    """Categorize key event into high-level category to avoid logging typed characters.

    Adheres to data minimization: literal characters (passwords, answers, prose)
    are NEVER stored in the database or transmitted across network boundaries.
    """
    if not key:
        return "other"

    if len(key) == 1:
        if ("a" <= key <= "z") or ("A" <= key <= "Z"):
            return "letter"
        if "0" <= key <= "9":
            return "digit"
        if key == " ":
            return "space"
        if key in ".,!?;:'\"()[]{}<>-=_+*/\\|@#$%^&~`":
            return "punctuation"
        return "other"

    lower = key.lower()
    if lower == "backspace":
        return "backspace"
    if lower in ("enter", "return"):
        return "enter"
    if lower == "tab":
        return "tab"
    if lower in ("shift", "control", "ctrl", "alt", "meta", "capslock"):
        return "modifier"
    if lower.startswith("arrow"):
        return "arrow"
    if lower in ("delete", "del"):
        return "delete"
    if lower in ("escape", "esc"):
        return "escape"
    return "other"


# -----------------------------------------------------------------------------
# Empirical Keystroke & Gaze Benchmark Dataset
# -----------------------------------------------------------------------------

BENCHMARK_PROFILES = {
    "letter": {"mean_dwell": 88.0, "std_dwell": 16.0, "mean_flight": 132.0, "std_flight": 30.0},
    "digit": {"mean_dwell": 96.0, "std_dwell": 18.0, "mean_flight": 150.0, "std_flight": 38.0},
    "space": {"mean_dwell": 78.0, "std_dwell": 14.0, "mean_flight": 120.0, "std_flight": 26.0},
    "backspace": {"mean_dwell": 110.0, "std_dwell": 22.0, "mean_flight": 170.0, "std_flight": 42.0},
    "enter": {"mean_dwell": 105.0, "std_dwell": 24.0, "mean_flight": 210.0, "std_flight": 55.0},
    "punctuation": {"mean_dwell": 94.0, "std_dwell": 19.0, "mean_flight": 158.0, "std_flight": 36.0},
    "modifier": {"mean_dwell": 130.0, "std_dwell": 35.0, "mean_flight": 140.0, "std_flight": 40.0},
    "other": {"mean_dwell": 95.0, "std_dwell": 20.0, "mean_flight": 145.0, "std_flight": 35.0},
}

# Curated reference sequence representing realistic student coding/assessment entry
BENCHMARK_HUMAN_KEYSTROKES: List[Dict[str, Any]] = [
    {"key_category": "letter", "dwell_ms": 86, "flight_ms": 130},
    {"key_category": "letter", "dwell_ms": 92, "flight_ms": 125},
    {"key_category": "letter", "dwell_ms": 80, "flight_ms": 140},
    {"key_category": "space", "dwell_ms": 74, "flight_ms": 115},
    {"key_category": "letter", "dwell_ms": 88, "flight_ms": 135},
    {"key_category": "letter", "dwell_ms": 94, "flight_ms": 128},
    {"key_category": "punctuation", "dwell_ms": 98, "flight_ms": 160},
    {"key_category": "space", "dwell_ms": 76, "flight_ms": 118},
    {"key_category": "letter", "dwell_ms": 85, "flight_ms": 132},
    {"key_category": "letter", "dwell_ms": 90, "flight_ms": 122},
    {"key_category": "backspace", "dwell_ms": 115, "flight_ms": 180},
    {"key_category": "letter", "dwell_ms": 88, "flight_ms": 140},
    {"key_category": "digit", "dwell_ms": 95, "flight_ms": 150},
    {"key_category": "digit", "dwell_ms": 98, "flight_ms": 145},
    {"key_category": "enter", "dwell_ms": 110, "flight_ms": 220},
]

# Synthetic robotic cadence anomaly sequence (macro / auto-typer)
BENCHMARK_ROBOTIC_KEYSTROKES: List[Dict[str, Any]] = [
    {"key_category": "letter", "dwell_ms": 45, "flight_ms": 80}
    for _ in range(25)
]

# Clipboard injection anomaly sequence
BENCHMARK_CLIPBOARD_KEYSTROKES: List[Dict[str, Any]] = [
    {"key_category": "letter", "dwell_ms": 10, "flight_ms": 1}
    for _ in range(20)
]

# Curated focused gaze calibration sequence
BENCHMARK_FOCUSED_GAZE: List[Dict[str, Any]] = [
    {"timestamp_ms": 1000 + i * 200, "gaze_x": 0.50 + ((i % 5) - 2) * 0.015, "gaze_y": 0.48 + ((i % 3) - 1) * 0.012, "confidence": 0.94, "off_screen": False}
    for i in range(20)
]

# Curated off-screen glance sequence
BENCHMARK_OFFSCREEN_GAZE: List[Dict[str, Any]] = [
    {"timestamp_ms": 1000 + i * 200, "gaze_x": 1.35, "gaze_y": 0.85, "confidence": 0.42, "off_screen": True}
    for i in range(15)
]


def generate_baseline_keystroke_features(n_samples: int = 150):
    """Generate realistic feature vectors [avg_dwell, std_dwell, avg_flight, std_flight]

    Calibrated against human benchmark distributions across multiple typist archetypes
    (fluent programmer, deliberate thinker, conversational respondent).
    Works with numpy or standard library random fallback.
    """
    try:
        import numpy as np

        rng = np.random.default_rng(seed=42)

        # 1. Fluent typists (~40% of baseline): fast, low dwell, tight flight
        n1 = int(n_samples * 0.40)
        d1 = rng.normal(loc=78.0, scale=10.0, size=(n1, 1))
        d1_std = rng.normal(loc=16.0, scale=3.5, size=(n1, 1))
        f1 = rng.normal(loc=115.0, scale=18.0, size=(n1, 1))
        f1_std = rng.normal(loc=28.0, scale=6.0, size=(n1, 1))
        c1 = np.hstack([d1, d1_std, f1, f1_std])

        # 2. Average balanced typists (~40% of baseline): standard pace
        n2 = int(n_samples * 0.40)
        d2 = rng.normal(loc=95.0, scale=14.0, size=(n2, 1))
        d2_std = rng.normal(loc=22.0, scale=5.0, size=(n2, 1))
        f2 = rng.normal(loc=145.0, scale=25.0, size=(n2, 1))
        f2_std = rng.normal(loc=38.0, scale=8.0, size=(n2, 1))
        c2 = np.hstack([d2, d2_std, f2, f2_std])

        # 3. Deliberate / thoughtful typists (~20% of baseline): longer pauses between clauses
        n3 = n_samples - n1 - n2
        d3 = rng.normal(loc=115.0, scale=18.0, size=(n3, 1))
        d3_std = rng.normal(loc=28.0, scale=6.0, size=(n3, 1))
        f3 = rng.normal(loc=185.0, scale=35.0, size=(n3, 1))
        f3_std = rng.normal(loc=52.0, scale=12.0, size=(n3, 1))
        c3 = np.hstack([d3, d3_std, f3, f3_std])

        data = np.vstack([c1, c2, c3])
        # Enforce physiological lower bounds (human finger press dwell cannot be < 25ms organically)
        data = np.clip(data, a_min=[25.0, 5.0, 30.0, 8.0], a_max=None)
        return data
    except ImportError:
        import random

        rng = random.Random(42)
        data = []
        for i in range(n_samples):
            if i < int(n_samples * 0.40):
                d = max(25.0, rng.gauss(78.0, 10.0))
                d_std = max(5.0, rng.gauss(16.0, 3.5))
                f = max(30.0, rng.gauss(115.0, 18.0))
                f_std = max(8.0, rng.gauss(28.0, 6.0))
            elif i < int(n_samples * 0.80):
                d = max(25.0, rng.gauss(95.0, 14.0))
                d_std = max(5.0, rng.gauss(22.0, 5.0))
                f = max(30.0, rng.gauss(145.0, 25.0))
                f_std = max(8.0, rng.gauss(38.0, 8.0))
            else:
                d = max(25.0, rng.gauss(115.0, 18.0))
                d_std = max(5.0, rng.gauss(28.0, 6.0))
                f = max(30.0, rng.gauss(185.0, 35.0))
                f_std = max(8.0, rng.gauss(52.0, 12.0))
            data.append([round(d, 2), round(d_std, 2), round(f, 2), round(f_std, 2)])
        return data


# -----------------------------------------------------------------------------
# Database Seeding Utility
# -----------------------------------------------------------------------------

def seed_monitoring_dataset(app_instance=None):
    """Seed sample candidates, assessment, and realistic monitoring sessions into DB."""
    # Ensure default user exists
    user = User.query.filter_by(email="student@example.test").first()
    if not user:
        user = User(
            identity_subject="demo-student-maya",
            email="student@example.test",
            status="active",
        )
        db.session.add(user)
        db.session.flush()

    # Ensure default assessment exists
    assessment = Assessment.query.filter_by(title="Java & Systems Engineering Assessment").first()
    if not assessment:
        assessment = Assessment(
            title="Java & Systems Engineering Assessment",
            description="Core assessment covering Java concurrency, Spring REST endpoints, and SQL queries.",
            duration_minutes=60,
        )
        db.session.add(assessment)
        db.session.flush()

    now = datetime.utcnow()
    created_sessions = []

    # 1. Verified Session: Maya Chen (Clean, compliant, verified consent)
    session_clean = MonitoringSession.query.filter_by(session_id="session-maya-chen-verified").first()
    if not session_clean:
        session_clean = MonitoringSession(
            session_id="session-maya-chen-verified",
            candidate_id=user.id,
            assessment_id=assessment.id,
            consent_given_at=now - timedelta(minutes=40),
            started_at=now - timedelta(minutes=40),
            ended_at=now - timedelta(minutes=5),
            retention_expires_at=now + timedelta(days=30),
        )
        db.session.add(session_clean)
        db.session.flush()

        # Seed derived gaze samples (calibrated on-screen)
        for i in range(40):
            sample = GazeSample(
                session_id=session_clean.id,
                timestamp_ms=int((now - timedelta(minutes=40) + timedelta(seconds=i * 2)).timestamp() * 1000),
                gaze_x=0.50 + ((i % 7) - 3) * 0.015,
                gaze_y=0.48 + ((i % 5) - 2) * 0.012,
                confidence=0.92 + (i % 3) * 0.02,
                off_screen=False,
            )
            db.session.add(sample)

        # Seed derived keystroke events (human typing dynamics)
        for i in range(50):
            category = ["letter", "letter", "letter", "space", "letter", "digit", "backspace"][i % 7]
            prof = BENCHMARK_PROFILES.get(category, BENCHMARK_PROFILES["letter"])
            ke = KeystrokeEvent(
                session_id=session_clean.id,
                key_category=category,
                dwell_ms=int(prof["mean_dwell"] + ((i % 5) - 2) * 4),
                flight_ms=int(prof["mean_flight"] + ((i % 7) - 3) * 8),
            )
            db.session.add(ke)

        created_sessions.append(session_clean.session_id)

    # 2. Flagged Session: Bot / Macro Typing Anomaly
    session_flagged = MonitoringSession.query.filter_by(session_id="session-candidate-flagged").first()
    if not session_flagged:
        session_flagged = MonitoringSession(
            session_id="session-candidate-flagged",
            candidate_id=user.id,
            assessment_id=assessment.id,
            consent_given_at=now - timedelta(minutes=20),
            started_at=now - timedelta(minutes=20),
            ended_at=now - timedelta(minutes=2),
            retention_expires_at=now + timedelta(days=30),
        )
        db.session.add(session_flagged)
        db.session.flush()

        # Seed derived gaze samples (repeated off-screen glances)
        for i in range(25):
            is_off = (i % 3 != 0)
            sample = GazeSample(
                session_id=session_flagged.id,
                timestamp_ms=int((now - timedelta(minutes=20) + timedelta(seconds=i * 2)).timestamp() * 1000),
                gaze_x=1.35 if is_off else 0.50,
                gaze_y=0.85 if is_off else 0.50,
                confidence=0.40 if is_off else 0.88,
                off_screen=is_off,
            )
            db.session.add(sample)

        # Seed robotic macro keystrokes (constant 45ms dwell, 80ms flight)
        for i in range(40):
            ke = KeystrokeEvent(
                session_id=session_flagged.id,
                key_category="letter",
                dwell_ms=45,
                flight_ms=80,
            )
            db.session.add(ke)

        created_sessions.append(session_flagged.session_id)

    db.session.commit()
    logger.info("Successfully seeded monitoring benchmark sessions: %s", created_sessions)
    return {
        "status": "seeded",
        "assessment_id": assessment.id,
        "candidate_id": user.id,
        "sessions_seeded": created_sessions,
    }


# -----------------------------------------------------------------------------
# Retention Cleanup Utility
# -----------------------------------------------------------------------------

def cleanup_expired_sessions() -> Dict[str, Any]:
    """Purge granular gaze samples and keystroke events whose retention period has expired.

    Minimizes legal and compliance footprint by automatically shredding derived telemetry
    once assessment reviews are finalized.
    """
    now = datetime.utcnow()
    expired_sessions = MonitoringSession.query.filter(
        MonitoringSession.retention_expires_at.isnot(None),
        MonitoringSession.retention_expires_at <= now,
    ).all()

    if not expired_sessions:
        return {
            "status": "clean",
            "expired_sessions_count": 0,
            "gaze_samples_purged": 0,
            "keystroke_events_purged": 0,
        }

    expired_ids = [s.id for s in expired_sessions]

    # Delete granular samples
    gaze_count = GazeSample.query.filter(GazeSample.session_id.in_(expired_ids)).delete(synchronize_session=False)
    keystroke_count = KeystrokeEvent.query.filter(KeystrokeEvent.session_id.in_(expired_ids)).delete(synchronize_session=False)

    # Mark sessions as expired/ended
    for s in expired_sessions:
        if not s.ended_at:
            s.ended_at = now

    db.session.commit()
    logger.info(
        "Purged %d gaze samples and %d keystroke events for %d expired sessions",
        gaze_count,
        keystroke_count,
        len(expired_ids),
    )

    return {
        "status": "purged",
        "expired_sessions_count": len(expired_ids),
        "gaze_samples_purged": gaze_count,
        "keystroke_events_purged": keystroke_count,
    }
