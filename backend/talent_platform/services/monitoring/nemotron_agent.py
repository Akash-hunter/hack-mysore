"""Nemotron 3.5 Lightning agent layer for synthesizing monitoring signals.

Nemotron sits above the gaze and keystroke plugins, taking raw numeric scores
and event telemetry and translating them into concise, recruiter-facing narrative
summaries and integrity risk evaluations.
"""

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NemotronMonitoringAgent:
    """Agent synthesis layer that generates recruiter-readable integrity reports."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "nvidia/nemotron-3.5-lightning",
        endpoint_url: str = "https://integrate.api.nvidia.com/v1/chat/completions",
    ):
        self.api_key = (
            api_key
            or os.environ.get("NEMOTRON_API_KEY")
            or os.environ.get("NVIDIA_API_KEY")
        )
        self.model_name = model_name
        self.endpoint_url = endpoint_url

    def synthesize_report(
        self,
        session_id: str,
        gaze_telemetry: List[dict],
        keystroke_telemetry: Optional[dict] = None,
        browser_signals: Optional[List[dict]] = None,
    ) -> dict:
        """Synthesize multimodal monitoring outputs into a recruiter-facing report.

        Args:
            session_id: Identifier of the candidate test session.
            gaze_telemetry: List of gaze results collected across frames.
            keystroke_telemetry: Output from score_session of a keystroke analyzer.
            browser_signals: List of browser events (tab switches, copy/paste, blur).

        Returns:
            dict containing:
                - integrity_verdict: str ('VERIFIED', 'MODERATE_RISK', 'HIGH_RISK')
                - risk_score: float (0.0 to 100.0)
                - narrative_summary: str
                - recruiter_bullets: list[str]
                - breakdown: dict of metrics
        """
        browser_signals = browser_signals or []
        keystroke_telemetry = keystroke_telemetry or {"anomaly_score": 0.0, "flags": [], "metrics": {}}

        # Aggregate Gaze Metrics
        total_gaze_frames = len(gaze_telemetry)
        off_screen_frames = sum(1 for g in gaze_telemetry if g.get("off_screen"))
        no_face_frames = sum(
            1
            for g in gaze_telemetry
            if "no_face_detected" in (g.get("details", {}).get("flags") or [])
        )
        off_screen_pct = (
            round((off_screen_frames / total_gaze_frames) * 100, 1)
            if total_gaze_frames > 0
            else 0.0
        )

        # Aggregate Browser Signals
        tab_switches = sum(1 for s in browser_signals if s.get("type") == "tab_switch")
        copy_pastes = sum(1 for s in browser_signals if s.get("type") == "copy_paste")
        focus_losts = sum(1 for s in browser_signals if s.get("type") == "focus_lost")

        # Aggregate Keystroke Metrics
        keystroke_anomaly = keystroke_telemetry.get("anomaly_score", 0.0)
        keystroke_flags = keystroke_telemetry.get("flags", [])
        keystroke_metrics = keystroke_telemetry.get("metrics", {})

        # Compute Composite Integrity Risk Score (0 - 100)
        risk_score = 0.0

        # Gaze contribution (up to 35 points)
        if off_screen_pct > 15.0:
            risk_score += min(30.0, (off_screen_pct - 15.0) * 1.5)
        if no_face_frames > 2:
            risk_score += min(15.0, no_face_frames * 3.0)

        # Keystroke contribution (up to 35 points)
        if "clipboard_injection" in keystroke_flags:
            risk_score += 25.0
        if "robotic_cadence" in keystroke_flags:
            risk_score += 30.0
        risk_score += min(20.0, keystroke_anomaly * 20.0)

        # Browser contribution (up to 30 points)
        risk_score += min(20.0, tab_switches * 6.0)
        risk_score += min(20.0, copy_pastes * 10.0)
        risk_score += min(10.0, focus_losts * 3.0)

        risk_score = min(100.0, round(risk_score, 1))

        # Determine Verdict
        if risk_score < 20.0:
            verdict = "VERIFIED"
        elif risk_score < 50.0:
            verdict = "MODERATE_RISK"
        else:
            verdict = "HIGH_RISK"

        # Attempt LLM synthesis if API key is present
        if self.api_key:
            llm_summary = self._call_nemotron_api(
                session_id=session_id,
                risk_score=risk_score,
                verdict=verdict,
                off_screen_pct=off_screen_pct,
                off_screen_frames=off_screen_frames,
                total_frames=total_gaze_frames,
                keystroke_flags=keystroke_flags,
                keystroke_metrics=keystroke_metrics,
                tab_switches=tab_switches,
                copy_pastes=copy_pastes,
            )
            if llm_summary:
                return llm_summary

        # Heuristic Narrative Generation (Deterministic Fallback)
        narrative, bullets = self._generate_heuristic_narrative(
            verdict=verdict,
            risk_score=risk_score,
            off_screen_pct=off_screen_pct,
            off_screen_frames=off_screen_frames,
            no_face_frames=no_face_frames,
            keystroke_flags=keystroke_flags,
            keystroke_metrics=keystroke_metrics,
            tab_switches=tab_switches,
            copy_pastes=copy_pastes,
        )

        return {
            "session_id": session_id,
            "integrity_verdict": verdict,
            "risk_score": risk_score,
            "narrative_summary": narrative,
            "recruiter_bullets": bullets,
            "breakdown": {
                "gaze": {
                    "total_frames": total_gaze_frames,
                    "off_screen_frames": off_screen_frames,
                    "off_screen_percentage": off_screen_pct,
                    "no_face_frames": no_face_frames,
                },
                "keystroke": {
                    "anomaly_score": keystroke_anomaly,
                    "flags": keystroke_flags,
                    "wpm_estimate": keystroke_metrics.get("wpm_estimate", 0),
                    "avg_dwell_ms": keystroke_metrics.get("avg_dwell_ms", 0),
                },
                "browser": {
                    "tab_switches": tab_switches,
                    "copy_pastes": copy_pastes,
                    "focus_lost_count": focus_losts,
                },
            },
        }

    def _generate_heuristic_narrative(
        self,
        verdict: str,
        risk_score: float,
        off_screen_pct: float,
        off_screen_frames: int,
        no_face_frames: int,
        keystroke_flags: List[str],
        keystroke_metrics: dict,
        tab_switches: int,
        copy_pastes: int,
    ) -> tuple[str, List[str]]:
        bullets = []

        # Gaze narrative
        if off_screen_frames == 0 and no_face_frames == 0:
            gaze_phrase = "Continuous visual screen focus maintained throughout session."
            bullets.append("Gaze: 100% on-screen fixation, no gaze anomalies detected.")
        elif off_screen_pct <= 10.0:
            gaze_phrase = f"{off_screen_frames} brief off-screen glance(s) detected ({off_screen_pct}% of session), consistent with normal cognitive pauses."
            bullets.append(f"Gaze: Normal cognitive glance behavior ({off_screen_pct}% off-screen).")
        else:
            gaze_phrase = f"Elevated off-screen gaze activity recorded ({off_screen_frames} frames, {off_screen_pct}% of total session)."
            bullets.append(f"Warning: Candidate looked away from screen during {off_screen_pct}% of checked frames.")

        # Keystroke narrative
        wpm = keystroke_metrics.get("wpm_estimate", 0)
        avg_dwell = keystroke_metrics.get("avg_dwell_ms", 0)
        if "robotic_cadence" in keystroke_flags:
            key_phrase = "Suspicious robotic keystroke cadence detected with near-zero latency variance, indicative of automated typing scripts."
            bullets.append("Keystroke Alert: Unnatural robotic typing cadence detected.")
        elif "clipboard_injection" in keystroke_flags:
            key_phrase = "Large burst of characters typed within milliseconds, indicating automated clipboard injection."
            bullets.append("Keystroke Alert: Potential unauthorized clipboard injection detected.")
        else:
            key_phrase = f"Typing rhythm was natural and consistent (avg dwell {avg_dwell}ms, ~{wpm} WPM)."
            bullets.append(f"Keystroke: Organic typing dynamics verified (~{wpm} WPM, natural dwell time).")

        # Browser narrative
        if tab_switches > 0 or copy_pastes > 0:
            browser_phrase = f"Browser monitoring logged {tab_switches} tab switch(es) and {copy_pastes} copy-paste event(s)."
            if tab_switches > 0:
                bullets.append(f"Browser: {tab_switches} tab switch event(s) logged during test.")
            if copy_pastes > 0:
                bullets.append(f"Browser: {copy_pastes} copy-paste event(s) captured.")
        else:
            browser_phrase = "No unauthorized browser tab switches or copy-paste operations detected."
            bullets.append("Browser: Window focus retained, zero unauthorized tab departures.")

        narrative = f"{gaze_phrase} {key_phrase} {browser_phrase}"
        return narrative, bullets

    def _call_nemotron_api(
        self,
        session_id: str,
        risk_score: float,
        verdict: str,
        off_screen_pct: float,
        off_screen_frames: int,
        total_frames: int,
        keystroke_flags: List[str],
        keystroke_metrics: dict,
        tab_switches: int,
        copy_pastes: int,
    ) -> Optional[dict]:
        """Optionally call NVIDIA Nemotron API when API key is configured."""
        try:
            prompt = (
                f"You are Nemotron 3.5 Lightning, an AI integrity agent reviewing proctoring telemetry.\n"
                f"Session ID: {session_id}\n"
                f"Telemetry:\n"
                f"- Total Gaze Frames: {total_frames}\n"
                f"- Off-Screen Glances: {off_screen_frames} ({off_screen_pct}%)\n"
                f"- Keystroke Flags: {keystroke_flags}\n"
                f"- Typing Speed: {keystroke_metrics.get('wpm_estimate')} WPM\n"
                f"- Tab Switches: {tab_switches}\n"
                f"- Copy/Pastes: {copy_pastes}\n"
                f"- Computed Risk Score: {risk_score}/100 ({verdict})\n\n"
                f"Generate a 2-sentence executive summary for the recruiter and 3 concise bullet points. "
                f"Respond in JSON format: {{\"narrative\": \"...\", \"bullets\": [\"...\", \"...\"]}}"
            )

            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 250,
            }

            req = urllib.request.Request(
                self.endpoint_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                return {
                    "session_id": session_id,
                    "integrity_verdict": verdict,
                    "risk_score": risk_score,
                    "narrative_summary": parsed.get("narrative"),
                    "recruiter_bullets": parsed.get("bullets", []),
                    "breakdown": {
                        "gaze": {"off_screen_percentage": off_screen_pct},
                        "keystroke": {"flags": keystroke_flags},
                        "browser": {"tab_switches": tab_switches, "copy_pastes": copy_pastes},
                    },
                }
        except Exception as e:
            logger.warning("Nemotron API call failed or timed out: %s. Using heuristic fallback.", e)
            return None
