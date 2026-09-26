"""Tests for pluggable monitoring backends, Nemotron agent, and live proctoring routes."""

import base64
import pytest
from talent_platform import create_app
from talent_platform.services.monitoring import (
    GAZE_BACKENDS,
    KEYSTROKE_BACKENDS,
    GazeTracker,
    KeystrokeAnalyzer,
    MediaPipeGazeTracker,
    L2CSGazeTracker,
    KNNKeystrokeAnalyzer,
    LSTMKeystrokeAnalyzer,
    NemotronMonitoringAgent,
    get_gaze_tracker,
    get_keystroke_analyzer,
    register_gaze_backend,
    register_keystroke_backend,
)
from app.services.integrity_engine import IntegrityEngine


# --- 1. Pluggable Architecture & Registration Tests ---

def test_backend_registries_and_factory():
    assert "mediapipe" in GAZE_BACKENDS
    assert "l2cs" in GAZE_BACKENDS
    assert "knn" in KEYSTROKE_BACKENDS
    assert "lstm" in KEYSTROKE_BACKENDS

    gaze_mp = get_gaze_tracker("mediapipe")
    assert isinstance(gaze_mp, MediaPipeGazeTracker)

    gaze_l2cs = get_gaze_tracker("l2cs")
    assert isinstance(gaze_l2cs, L2CSGazeTracker)

    key_knn = get_keystroke_analyzer("knn")
    assert isinstance(key_knn, KNNKeystrokeAnalyzer)

    key_lstm = get_keystroke_analyzer("lstm")
    assert isinstance(key_lstm, LSTMKeystrokeAnalyzer)


def test_invalid_backend_name_raises():
    with pytest.raises(ValueError, match="Unknown gaze backend"):
        get_gaze_tracker("non_existent_backend")

    with pytest.raises(ValueError, match="Unknown keystroke backend"):
        get_keystroke_analyzer("non_existent_backend")


def test_custom_plugin_registration():
    class CustomGazeTracker(GazeTracker):
        def process_frame(self, frame_bytes: bytes) -> dict:
            return {"gaze_x": 0.0, "gaze_y": 0.0, "confidence": 1.0, "off_screen": False}

    register_gaze_backend("custom_gaze", CustomGazeTracker)
    tracker = get_gaze_tracker("custom_gaze")
    assert isinstance(tracker, CustomGazeTracker)
    res = tracker.process_frame(b"test")
    assert res["confidence"] == 1.0

    class CustomKeyAnalyzer(KeystrokeAnalyzer):
        def score_session(self, keystroke_events: list[dict]) -> dict:
            return {"anomaly_score": 0.05, "flags": []}

    register_keystroke_backend("custom_key", CustomKeyAnalyzer)
    analyzer = get_keystroke_analyzer("custom_key")
    assert isinstance(analyzer, CustomKeyAnalyzer)
    res = analyzer.score_session([])
    assert res["anomaly_score"] == 0.05


# --- 2. Gaze Tracker Tests ---

def test_mediapipe_empty_and_fallback_frames():
    tracker = MediaPipeGazeTracker()

    # Empty frame test
    empty_res = tracker.process_frame(b"")
    assert empty_res["off_screen"] is True
    assert empty_res["confidence"] == 0.0

    # Normal centered fallback frame
    normal_res = tracker.process_frame(b"JPEG_MOCK_NORMAL_FRAME")
    assert "gaze_x" in normal_res
    assert "gaze_y" in normal_res
    assert normal_res["off_screen"] is False
    assert normal_res["confidence"] > 0.5

    # Simulated off-screen glance
    off_res = tracker.process_frame(b"TEST_OFF_SCREEN_DATA")
    assert off_res["off_screen"] is True
    assert "off_screen_gaze" in off_res["details"]["flags"]

    # Simulated no-face frame
    no_face_res = tracker.process_frame(b"TEST_NO_FACE_DATA")
    assert no_face_res["off_screen"] is True
    assert no_face_res["confidence"] == 0.0
    assert "no_face_detected" in no_face_res["details"]["flags"]


def test_l2cs_gaze_tracker():
    tracker = L2CSGazeTracker()

    res = tracker.process_frame(b"NORMAL_FRAME")
    assert res["confidence"] > 0.8
    assert res["off_screen"] is False

    off_res = tracker.process_frame(b"TEST_OFF_SCREEN_FRAME")
    assert off_res["off_screen"] is True
    assert "pitch_deg" in off_res["details"]


# --- 3. Keystroke Dynamics Analyzer Tests ---

def test_knn_insufficient_data():
    analyzer = KNNKeystrokeAnalyzer(min_events_required=5)
    res = analyzer.score_session([{"key": "a", "down_time": 100, "up_time": 180}])
    assert res["anomaly_score"] == 0.0
    assert res["metrics"]["status"] == "insufficient_data"


def test_knn_organic_human_typing():
    analyzer = KNNKeystrokeAnalyzer()

    # Generate organic typing pattern: ~90ms dwell, ~130ms flight with natural jitter
    events = []
    current_time = 1000.0
    for i, char in enumerate("The quick brown fox jumps over the lazy dog"):
        dwell = 85.0 + (i % 7) * 4.0  # slight organic variation
        flight = 120.0 + (i % 5) * 8.0
        events.append({
            "key": char,
            "down_time": current_time,
            "up_time": current_time + dwell,
        })
        current_time += dwell + flight

    res = analyzer.score_session(events)
    assert res["anomaly_score"] < 0.55
    assert "robotic_cadence" not in res["flags"]
    assert "clipboard_injection" not in res["flags"]
    assert res["metrics"]["events_count"] == len(events)
    assert res["metrics"]["wpm_estimate"] > 0


def test_knn_robotic_macro_detection():
    analyzer = KNNKeystrokeAnalyzer()

    # Robotic typing has exactly identical millisecond precision
    events = []
    current_time = 1000.0
    for i in range(25):
        events.append({
            "key": chr(ord('a') + (i % 26)),
            "down_time": current_time,
            "up_time": current_time + 50.000,  # Exact 50.0ms every time
        })
        current_time += 50.000 + 100.000  # Exact 100.0ms flight every time

    res = analyzer.score_session(events)
    assert "robotic_cadence" in res["flags"]
    assert res["anomaly_score"] >= 0.80


def test_knn_clipboard_injection_detection():
    analyzer = KNNKeystrokeAnalyzer()

    # Instant clipboard burst: 20 characters arriving within 1ms flights
    events = []
    current_time = 2000.0
    for i in range(20):
        events.append({
            "key": "x",
            "down_time": current_time,
            "up_time": current_time + 10.0,
        })
        current_time += 1.0  # Superhuman 1ms latency

    res = analyzer.score_session(events)
    assert "clipboard_injection" in res["flags"]
    assert res["anomaly_score"] >= 0.85


def test_lstm_keystroke_analyzer():
    analyzer = LSTMKeystrokeAnalyzer()

    # Normal sequence
    normal_events = [
        {"down_time": 1.0 + i * 0.15 + (i % 3) * 0.02} for i in range(10)
    ]
    res = analyzer.score_session(normal_events)
    assert res["anomaly_score"] < 0.4

    # Repeating macro sequence
    macro_events = [{"down_time": 1.0 + i * 0.05} for i in range(10)]
    macro_res = analyzer.score_session(macro_events)
    assert "recurrent_macro_sequence" in macro_res["flags"]
    assert macro_res["anomaly_score"] >= 0.8


# --- 4. Nemotron Agent Synthesis Tests ---

def test_nemotron_verified_session():
    agent = NemotronMonitoringAgent()

    # Candidate with 10 on-screen frames, natural typing, 0 tab switches
    gaze_telemetry = [{"off_screen": False} for _ in range(10)]
    keystroke_telemetry = {
        "anomaly_score": 0.05,
        "flags": [],
        "metrics": {"wpm_estimate": 68.0, "avg_dwell_ms": 88.0},
    }
    browser_signals = []

    report = agent.synthesize_report(
        session_id="session-101",
        gaze_telemetry=gaze_telemetry,
        keystroke_telemetry=keystroke_telemetry,
        browser_signals=browser_signals,
    )

    assert report["session_id"] == "session-101"
    assert report["integrity_verdict"] == "VERIFIED"
    assert report["risk_score"] < 20.0
    assert "Continuous visual screen focus" in report["narrative_summary"]
    assert len(report["recruiter_bullets"]) >= 3


def test_nemotron_high_risk_session():
    agent = NemotronMonitoringAgent()

    # Candidate looking off screen 8 out of 10 times, robotic keystrokes, 3 tab switches
    gaze_telemetry = [{"off_screen": True} for _ in range(8)] + [{"off_screen": False} for _ in range(2)]
    keystroke_telemetry = {
        "anomaly_score": 0.92,
        "flags": ["robotic_cadence"],
        "metrics": {"wpm_estimate": 140.0, "avg_dwell_ms": 30.0},
    }
    browser_signals = [
        {"type": "tab_switch", "duration": 5},
        {"type": "tab_switch", "duration": 8},
        {"type": "copy_paste"},
    ]

    report = agent.synthesize_report(
        session_id="session-suspicious",
        gaze_telemetry=gaze_telemetry,
        keystroke_telemetry=keystroke_telemetry,
        browser_signals=browser_signals,
    )

    assert report["session_id"] == "session-suspicious"
    assert report["integrity_verdict"] == "HIGH_RISK"
    assert report["risk_score"] >= 50.0
    assert any("Keystroke Alert" in b for b in report["recruiter_bullets"])
    assert any("tab switch" in b.lower() for b in report["recruiter_bullets"])


# --- 5. IntegrityEngine Bridge Tests ---

def test_integrity_engine_multimodal_signals():
    class MockSession:
        def __init__(self, signals):
            self.integrity_signals = signals
            self.integrity_risk_score = 0.0

    session = MockSession([
        {"type": "off_screen_gaze", "duration": 4.0},
        {"type": "no_face_detected"},
        {"type": "clipboard_injection"},
        {"type": "tab_switch", "duration": 10.0},
    ])

    score = IntegrityEngine.analyze_signals(session)
    assert score >= 40.0
    assert session.integrity_risk_score == score


# --- 6. Flask Live Proctoring Route Integration Tests ---

@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    return app.test_client()


def test_api_list_backends(client):
    res = client.get("/api/monitoring/backends")
    assert res.status_code == 200
    data = res.get_json()
    assert "mediapipe" in data["gaze_backends"]
    assert "l2cs" in data["gaze_backends"]
    assert "knn" in data["keystroke_backends"]
    assert data["agent"] == "nemotron-3.5-lightning"


def test_api_session_gaze_ingestion(client):
    session_id = "test-live-session-01"

    # Reset
    client.post(f"/api/monitoring/session/{session_id}/reset")

    # Ingest JSON frame
    res = client.post(
        f"/api/monitoring/session/{session_id}/gaze",
        json={"frame_base64": base64.b64encode(b"MOCK_FRAME").decode("utf-8"), "backend": "mediapipe"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["session_id"] == session_id
    assert "gaze_x" in data
    assert "gaze_y" in data
    assert "off_screen" in data


def test_api_session_keystroke_ingestion(client):
    session_id = "test-live-session-02"

    events = [
        {"key": "a", "down_time": 1000, "up_time": 1090},
        {"key": "b", "down_time": 1210, "up_time": 1300},
        {"key": "c", "down_time": 1420, "up_time": 1510},
        {"key": "d", "down_time": 1630, "up_time": 1720},
        {"key": "e", "down_time": 1840, "up_time": 1930},
        {"key": "f", "down_time": 2050, "up_time": 2140},
    ]

    res = client.post(
        f"/api/monitoring/session/{session_id}/keystroke",
        json={"events": events, "backend": "knn"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["session_id"] == session_id
    assert "anomaly_score" in data
    assert "flags" in data


def test_api_session_report_generation(client):
    session_id = "test-live-session-03"

    # Ingest gaze
    client.post(
        f"/api/monitoring/session/{session_id}/gaze",
        json={"frame_base64": base64.b64encode(b"FRAME_1").decode("utf-8")},
    )

    # Ingest browser signal
    client.post(
        f"/api/monitoring/session/{session_id}/browser-signal",
        json={"type": "tab_switch", "duration": 2},
    )

    # Ingest keystrokes
    events = [
        {"key": "x", "down_time": 100, "up_time": 190},
        {"key": "y", "down_time": 300, "up_time": 380},
        {"key": "z", "down_time": 500, "up_time": 590},
        {"key": "a", "down_time": 700, "up_time": 790},
        {"key": "b", "down_time": 900, "up_time": 990},
    ]
    client.post(
        f"/api/monitoring/session/{session_id}/keystroke",
        json={"events": events},
    )

    # Generate synthesis report
    res = client.get(f"/api/monitoring/session/{session_id}/report")
    assert res.status_code == 200
    report = res.get_json()
    assert report["session_id"] == session_id
    assert report["integrity_verdict"] in ["VERIFIED", "MODERATE_RISK", "HIGH_RISK"]
    assert "narrative_summary" in report
    assert "recruiter_bullets" in report
    assert "breakdown" in report
