"""In-memory telemetry buffer and session management for live proctoring sessions."""

from datetime import datetime, timedelta
import threading
import time
from typing import Any, Dict, List, Optional


class ProctoringSessionStore:
    """Thread-safe store holding ongoing live session telemetry buffers and consent state."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    "session_id": session_id,
                    "created_at": time.time(),
                    "consent_given_at": None,
                    "candidate_id": None,
                    "assessment_id": None,
                    "retention_expires_at": None,
                    "gaze_frames": [],
                    "keystroke_batches": [],
                    "browser_signals": [],
                    "latest_keystroke_result": None,
                }
            return self._sessions[session_id]

    def set_consent(
        self,
        session_id: str,
        candidate_id: Optional[int] = None,
        assessment_id: Optional[int] = None,
        retention_days: int = 30,
    ) -> Dict[str, Any]:
        with self._lock:
            now = datetime.utcnow()
            retention_date = now + timedelta(days=retention_days)
            session = self._sessions.setdefault(session_id, {
                "session_id": session_id,
                "created_at": time.time(),
                "consent_given_at": None,
                "candidate_id": None,
                "assessment_id": None,
                "retention_expires_at": None,
                "gaze_frames": [],
                "keystroke_batches": [],
                "browser_signals": [],
                "latest_keystroke_result": None,
            })
            session["consent_given_at"] = now.isoformat()
            session["candidate_id"] = candidate_id
            session["assessment_id"] = assessment_id
            session["retention_expires_at"] = retention_date.isoformat()
            return {
                "session_id": session_id,
                "consent_given": True,
                "consent_given_at": session["consent_given_at"],
                "candidate_id": candidate_id,
                "assessment_id": assessment_id,
                "retention_expires_at": session["retention_expires_at"],
            }

    def has_consent(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            return session.get("consent_given_at") is not None

    def add_gaze_frame(self, session_id: str, gaze_data: dict) -> None:
        with self._lock:
            session = self._sessions.setdefault(session_id, {
                "session_id": session_id,
                "created_at": time.time(),
                "consent_given_at": None,
                "candidate_id": None,
                "assessment_id": None,
                "retention_expires_at": None,
                "gaze_frames": [],
                "keystroke_batches": [],
                "browser_signals": [],
                "latest_keystroke_result": None,
            })
            session["gaze_frames"].append(gaze_data)

    def set_keystroke_result(self, session_id: str, events: list, result: dict) -> None:
        with self._lock:
            session = self._sessions.setdefault(session_id, {
                "session_id": session_id,
                "created_at": time.time(),
                "consent_given_at": None,
                "candidate_id": None,
                "assessment_id": None,
                "retention_expires_at": None,
                "gaze_frames": [],
                "keystroke_batches": [],
                "browser_signals": [],
                "latest_keystroke_result": None,
            })
            session["keystroke_batches"].append({"count": len(events), "timestamp": time.time()})
            session["latest_keystroke_result"] = result

    def add_browser_signal(self, session_id: str, signal: dict) -> None:
        with self._lock:
            session = self._sessions.setdefault(session_id, {
                "session_id": session_id,
                "created_at": time.time(),
                "consent_given_at": None,
                "candidate_id": None,
                "assessment_id": None,
                "retention_expires_at": None,
                "gaze_frames": [],
                "keystroke_batches": [],
                "browser_signals": [],
                "latest_keystroke_result": None,
            })
            session["browser_signals"].append({**signal, "timestamp": time.time()})

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._sessions.get(session_id)

    def reset_session(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]


# Global singleton instance
session_store = ProctoringSessionStore()
