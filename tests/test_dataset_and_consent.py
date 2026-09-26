"""Comprehensive tests for data minimization, consent gates, retention cleanup, and benchmark dataset."""

from datetime import datetime, timedelta
import pytest
from talent_platform import create_app, db
from talent_platform.models import User
from talent_platform.models.monitoring import (
    Assessment,
    GazeSample,
    KeystrokeEvent,
    MonitoringSession,
)
from talent_platform.services.monitoring.dataset import (
    categorize_key,
    cleanup_expired_sessions,
    generate_baseline_keystroke_features,
    seed_monitoring_dataset,
    BENCHMARK_PROFILES,
    BENCHMARK_HUMAN_KEYSTROKES,
)


@pytest.fixture
def app():
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# =============================================================================
# 1. Data Minimization & Model Schema Tests
# =============================================================================

def test_data_minimization_model_attributes(app):
    """Verify that models enforce data minimization: NO raw video frames, NO literal keys."""
    with app.app_context():
        # Check GazeSample columns
        gaze_cols = [c.name for c in GazeSample.__table__.columns]
        assert "gaze_x" in gaze_cols
        assert "gaze_y" in gaze_cols
        assert "confidence" in gaze_cols
        assert "off_screen" in gaze_cols
        assert "timestamp_ms" in gaze_cols
        # Data minimization guarantees:
        assert "raw_frame" not in gaze_cols
        assert "image_bytes" not in gaze_cols
        assert "video" not in gaze_cols

        # Check KeystrokeEvent columns
        key_cols = [c.name for c in KeystrokeEvent.__table__.columns]
        assert "key_category" in key_cols
        assert "dwell_ms" in key_cols
        assert "flight_ms" in key_cols
        # Data minimization guarantees:
        assert "literal_key" not in key_cols
        assert "key_char" not in key_cols
        assert "text" not in key_cols


def test_monitoring_models_relationships(app):
    """Verify MonitoringSession, Assessment, GazeSample, and KeystrokeEvent relationships."""
    with app.app_context():
        user = User(identity_subject="sub-eval-1", email="student.eval@example.test")
        assessment = Assessment(
            title="Backend Engineering Test",
            description="Algorithmic problem solving and SQL fundamentals.",
            duration_minutes=45,
        )
        db.session.add_all([user, assessment])
        db.session.commit()

        now = datetime.utcnow()
        session = MonitoringSession(
            session_id="eval-session-001",
            candidate_id=user.id,
            assessment_id=assessment.id,
            consent_given_at=now,
            started_at=now,
            retention_expires_at=now + timedelta(days=30),
        )
        db.session.add(session)
        db.session.commit()

        # Add derived gaze sample
        sample = GazeSample(
            session_id=session.id,
            timestamp_ms=1700000000000,
            gaze_x=0.52,
            gaze_y=0.49,
            confidence=0.96,
            off_screen=False,
        )
        # Add derived keystroke event
        keystroke = KeystrokeEvent(
            session_id=session.id,
            key_category="letter",
            dwell_ms=88,
            flight_ms=132,
        )
        db.session.add_all([sample, keystroke])
        db.session.commit()

        # Verify queries and navigation
        fetched_session = MonitoringSession.query.filter_by(session_id="eval-session-001").first()
        assert fetched_session is not None
        assert fetched_session.candidate.email == "student.eval@example.test"
        assert fetched_session.assessment.title == "Backend Engineering Test"
        assert fetched_session.gaze_samples.count() == 1
        assert fetched_session.keystroke_events.count() == 1

        gaze_dict = fetched_session.gaze_samples.first().to_dict()
        assert gaze_dict["gaze_x"] == 0.52
        assert gaze_dict["off_screen"] is False

        key_dict = fetched_session.keystroke_events.first().to_dict()
        assert key_dict["key_category"] == "letter"
        assert key_dict["dwell_ms"] == 88


# =============================================================================
# 2. Key Categorization & Privacy Transform Tests
# =============================================================================

def test_categorize_key_scrubs_content():
    """Verify that literal characters are scrubbed into privacy-preserving categories."""
    assert categorize_key("a") == "letter"
    assert categorize_key("Z") == "letter"
    assert categorize_key("9") == "digit"
    assert categorize_key("0") == "digit"
    assert categorize_key(" ") == "space"
    assert categorize_key("Backspace") == "backspace"
    assert categorize_key("Enter") == "enter"
    assert categorize_key("Return") == "enter"
    assert categorize_key("Tab") == "tab"
    assert categorize_key("Shift") == "modifier"
    assert categorize_key("Control") == "modifier"
    assert categorize_key("Alt") == "modifier"
    assert categorize_key("ArrowLeft") == "arrow"
    assert categorize_key("Delete") == "delete"
    assert categorize_key(".") == "punctuation"
    assert categorize_key(";") == "punctuation"
    assert categorize_key(None) == "other"


# =============================================================================
# 3. Consent Gate & API Enforcement Tests
# =============================================================================

def test_consent_gate_enforcement(client, app):
    """Test that telemetry is blocked before consent and accepted after consent."""
    session_id = "test-consent-session-01"

    # 1. Reset & verify no consent given initially
    client.post(f"/api/monitoring/session/{session_id}/reset")
    status_res = client.get(f"/api/monitoring/session/{session_id}/consent")
    assert status_res.status_code == 200
    assert status_res.get_json()["consent_given"] is False

    # 2. Telemetry with require_consent=true must be rejected with 403 Forbidden
    blocked_gaze = client.post(
        f"/api/monitoring/session/{session_id}/gaze?require_consent=true",
        json={"gaze_x": 0.5, "gaze_y": 0.5},
    )
    assert blocked_gaze.status_code == 403
    assert blocked_gaze.get_json()["code"] == "CONSENT_REQUIRED"

    blocked_key = client.post(
        f"/api/monitoring/session/{session_id}/keystroke?require_consent=true",
        json={"events": [{"key": "a", "down_time": 100, "up_time": 180}]},
    )
    assert blocked_key.status_code == 403
    assert blocked_key.get_json()["code"] == "CONSENT_REQUIRED"

    # 3. Grant explicit consent via POST /consent
    consent_res = client.post(
        f"/api/monitoring/session/{session_id}/consent",
        json={"consent": True, "retention_days": 14},
    )
    assert consent_res.status_code == 200
    data = consent_res.get_json()
    assert data["status"] == "consent_granted"
    assert data["consent_given"] is True
    assert data["consent_given_at"] is not None
    assert data["retention_expires_at"] is not None

    # 4. Now telemetry should be accepted successfully
    ok_gaze = client.post(
        f"/api/monitoring/session/{session_id}/gaze?require_consent=true",
        json={"gaze_x": 0.51, "gaze_y": 0.49, "confidence": 0.94},
    )
    assert ok_gaze.status_code == 200
    assert ok_gaze.get_json()["gaze_x"] == 0.51

    ok_key = client.post(
        f"/api/monitoring/session/{session_id}/keystroke?require_consent=true",
        json={"events": [
            {"key_category": "letter", "dwell_ms": 85, "flight_ms": 120},
            {"key_category": "space", "dwell_ms": 70, "flight_ms": 110},
            {"key_category": "letter", "dwell_ms": 88, "flight_ms": 125},
            {"key_category": "letter", "dwell_ms": 90, "flight_ms": 130},
            {"key_category": "letter", "dwell_ms": 84, "flight_ms": 120},
        ]},
    )
    assert ok_key.status_code == 200
    assert "anomaly_score" in ok_key.get_json()


# =============================================================================
# 4. Retention Policy & Data Cleanup Tests
# =============================================================================

def test_retention_cleanup_purges_expired_samples(app):
    """Test that retention cleanup permanently shreds samples for expired sessions."""
    with app.app_context():
        user = User(identity_subject="sub-retention", email="retention@example.test")
        db.session.add(user)
        db.session.commit()

        now = datetime.utcnow()

        # Session 1: Expired (retention period ended 2 days ago)
        expired_session = MonitoringSession(
            session_id="session-expired-01",
            candidate_id=user.id,
            consent_given_at=now - timedelta(days=35),
            started_at=now - timedelta(days=35),
            retention_expires_at=now - timedelta(days=2),
        )
        db.session.add(expired_session)
        db.session.commit()

        # Add 5 gaze samples and 5 keystroke events to expired session
        for i in range(5):
            db.session.add(GazeSample(
                session_id=expired_session.id,
                timestamp_ms=1000 + i * 200,
                gaze_x=0.5,
                gaze_y=0.5,
                confidence=0.9,
            ))
            db.session.add(KeystrokeEvent(
                session_id=expired_session.id,
                key_category="letter",
                dwell_ms=80,
                flight_ms=120,
            ))

        # Session 2: Active (retention expires in 28 days)
        active_session = MonitoringSession(
            session_id="session-active-02",
            candidate_id=user.id,
            consent_given_at=now,
            started_at=now,
            retention_expires_at=now + timedelta(days=28),
        )
        db.session.add(active_session)
        db.session.commit()

        # Add 3 gaze samples and 3 keystroke events to active session
        for i in range(3):
            db.session.add(GazeSample(
                session_id=active_session.id,
                timestamp_ms=2000 + i * 200,
                gaze_x=0.5,
                gaze_y=0.5,
                confidence=0.9,
            ))
            db.session.add(KeystrokeEvent(
                session_id=active_session.id,
                key_category="digit",
                dwell_ms=90,
                flight_ms=140,
            ))

        db.session.commit()

        # Before cleanup: verify counts
        assert GazeSample.query.count() == 8
        assert KeystrokeEvent.query.count() == 8

        # Run retention cleanup
        result = cleanup_expired_sessions()
        assert result["status"] == "purged"
        assert result["expired_sessions_count"] == 1
        assert result["gaze_samples_purged"] == 5
        assert result["keystroke_events_purged"] == 5

        # After cleanup: only active session samples remain
        assert GazeSample.query.count() == 3
        assert KeystrokeEvent.query.count() == 3
        remaining_samples = GazeSample.query.all()
        assert all(s.session_id == active_session.id for s in remaining_samples)


def test_retention_cleanup_api_route(client, app):
    """Test POST /api/monitoring/cleanup endpoint."""
    res = client.post("/api/monitoring/cleanup")
    assert res.status_code == 200
    data = res.get_json()
    assert "expired_sessions_count" in data
    assert "gaze_samples_purged" in data


# =============================================================================
# 5. Benchmark Dataset & Seeding Tests
# =============================================================================

def test_dataset_benchmark_profiles_and_endpoint(client):
    """Test benchmark distribution retrieval."""
    assert "letter" in BENCHMARK_PROFILES
    assert "digit" in BENCHMARK_PROFILES
    assert len(BENCHMARK_HUMAN_KEYSTROKES) >= 10

    res = client.get("/api/monitoring/dataset/benchmark")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "benchmark_profiles" in data
    assert "sample_sequences" in data
    assert data["policy"]["principles"] is not None


def test_dataset_seeding_service_and_api(client, app):
    """Test seeding database with demo candidate sessions."""
    res = client.post("/api/monitoring/dataset/seed")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "seeded"
    assert "session-maya-chen-verified" in data["sessions_seeded"]

    # Verify seeded session can be queried via /samples endpoint
    samples_res = client.get("/api/monitoring/session/session-maya-chen-verified/samples")
    assert samples_res.status_code == 200
    samples_data = samples_res.get_json()
    assert samples_data["data_minimization_verified"] is True
    assert samples_data["gaze_samples_count"] > 0
    assert samples_data["keystroke_events_count"] > 0
    # Confirm NO literal key text in keystroke events
    for ke in samples_data["keystroke_events"]:
        assert "key_category" in ke
        assert "key" not in ke
        assert "literal_key" not in ke


def test_baseline_features_generator():
    """Test empirical feature vector generator for KNN classifier."""
    features = generate_baseline_keystroke_features(n_samples=50)
    assert features is not None
    if hasattr(features, "shape"):
        assert features.shape == (50, 4)
        assert (features[:, 0] >= 25.0).all()
        assert (features[:, 2] >= 30.0).all()
    else:
        assert len(features) == 50
        assert len(features[0]) == 4
        assert all(row[0] >= 25.0 for row in features)
        assert all(row[2] >= 30.0 for row in features)


# =============================================================================
# 6. Static Client Capture Script Delivery Tests
# =============================================================================

def test_client_capture_scripts_accessible(client):
    """Verify that browser client capture scripts are served correctly."""
    gaze_script = client.get("/static/gaze_capture.js")
    assert gaze_script.status_code == 200
    assert b"GazeCaptureClient" in gaze_script.data
    assert b"mapLandmarksToScreen" in gaze_script.data

    key_script = client.get("/static/keystroke_capture.js")
    assert key_script.status_code == 200
    assert b"KeystrokeCaptureClient" in key_script.data
    assert b"categorizeKey" in key_script.data

    consent_script = client.get("/static/consent_gate.js")
    assert consent_script.status_code == 200
    assert b"ProctoringConsentGate" in consent_script.data
    assert b"DATA MINIMIZATION PROCTORING" in consent_script.data
