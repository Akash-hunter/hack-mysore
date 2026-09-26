"""Flask routes for live proctoring sessions."""

import base64
import logging
from flask import Blueprint, jsonify, request
from . import (
    GAZE_BACKENDS,
    KEYSTROKE_BACKENDS,
    get_gaze_tracker,
    get_keystroke_analyzer,
    NemotronMonitoringAgent,
)
from .session_store import session_store

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint("monitoring", __name__)


@monitoring_bp.get("/backends")
def list_backends():
    """List available pluggable backends for gaze and keystroke analysis."""
    return jsonify({
        "status": "ok",
        "gaze_backends": list(GAZE_BACKENDS.keys()),
        "keystroke_backends": list(KEYSTROKE_BACKENDS.keys()),
        "default_gaze": "mediapipe",
        "default_keystroke": "knn",
        "agent": "nemotron-3.5-lightning",
    }), 200


@monitoring_bp.post("/session/<session_id>/gaze")
def ingest_gaze_frame(session_id: str):
    """Ingest a webcam video frame, process with gaze tracker, and return coordinates."""
    backend_name = request.args.get("backend") or "mediapipe"
    frame_bytes = None

    # Support multipart/form-data file upload
    if "frame" in request.files:
        frame_bytes = request.files["frame"].read()
    elif request.is_json:
        data = request.get_json() or {}
        backend_name = data.get("backend", backend_name)
        base64_str = data.get("frame_base64")
        if base64_str:
            if "," in base64_str:
                base64_str = base64_str.split(",", 1)[1]
            try:
                frame_bytes = base64.b64decode(base64_str)
            except Exception as e:
                return jsonify({"error": f"Invalid base64 payload: {str(e)}"}), 400
    elif request.data:
        frame_bytes = request.data

    if not frame_bytes:
        return jsonify({"error": "No frame data provided. Send raw bytes, multipart 'frame', or JSON 'frame_base64'"}), 400

    try:
        tracker = get_gaze_tracker(backend_name)
        result = tracker.process_frame(frame_bytes)
        # Record into session telemetry buffer
        session_store.add_gaze_frame(session_id, result)

        return jsonify({
            "session_id": session_id,
            "status": "ok",
            **result,
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("Error processing gaze frame: %s", e)
        return jsonify({"error": f"Internal error processing frame: {str(e)}"}), 500


@monitoring_bp.post("/session/<session_id>/keystroke")
def ingest_keystrokes(session_id: str):
    """Ingest keystroke events batch and evaluate timing dynamics anomalies."""
    if not request.is_json:
        return jsonify({"error": "Expected JSON payload with 'events' array"}), 400

    data = request.get_json() or {}
    events = data.get("events", [])
    backend_name = data.get("backend") or request.args.get("backend") or "knn"

    if not isinstance(events, list):
        return jsonify({"error": "'events' must be an array of keystroke records"}), 400

    try:
        analyzer = get_keystroke_analyzer(backend_name)
        result = analyzer.score_session(events)
        # Record into session buffer
        session_store.set_keystroke_result(session_id, events, result)

        return jsonify({
            "session_id": session_id,
            "status": "ok",
            **result,
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("Error analyzing keystroke events: %s", e)
        return jsonify({"error": f"Internal error analyzing keystrokes: {str(e)}"}), 500


@monitoring_bp.post("/session/<session_id>/browser-signal")
def ingest_browser_signal(session_id: str):
    """Log browser-side integrity signals (tab switches, focus loss, copy-paste)."""
    if not request.is_json:
        return jsonify({"error": "Expected JSON payload with 'type'"}), 400

    signal = request.get_json() or {}
    if "type" not in signal:
        return jsonify({"error": "Signal must include 'type' (e.g. 'tab_switch', 'copy_paste')"}), 400

    session_store.add_browser_signal(session_id, signal)
    return jsonify({"session_id": session_id, "status": "signal_recorded"}), 200


@monitoring_bp.get("/session/<session_id>/report")
def get_session_report(session_id: str):
    """Generate a recruiter-facing synthesis report via the Nemotron agent layer."""
    session = session_store.get_session(session_id)
    if not session:
        # Generate clean baseline report for new/empty session
        session = session_store.get_or_create(session_id)

    gaze_telemetry = session.get("gaze_frames", [])
    keystroke_telemetry = session.get("latest_keystroke_result") or {"anomaly_score": 0.0, "flags": [], "metrics": {}}
    browser_signals = session.get("browser_signals", [])

    agent = NemotronMonitoringAgent()
    report = agent.synthesize_report(
        session_id=session_id,
        gaze_telemetry=gaze_telemetry,
        keystroke_telemetry=keystroke_telemetry,
        browser_signals=browser_signals,
    )

    return jsonify(report), 200


@monitoring_bp.post("/session/<session_id>/reset")
def reset_session(session_id: str):
    """Reset telemetry buffer for a given session."""
    session_store.reset_session(session_id)
    return jsonify({"session_id": session_id, "status": "reset_successful"}), 200
