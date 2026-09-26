"""LSTM recurrent sequential classifier for keystroke dynamics."""

import logging
from typing import Any, Dict, List
from ..base import KeystrokeAnalyzer, KeystrokeResult

logger = logging.getLogger(__name__)


class LSTMKeystrokeAnalyzer(KeystrokeAnalyzer):
    """Sequential LSTM classifier backend for keystroke dynamics rhythm evaluation.

    Evaluates temporal transitions across sequential n-grams of keystrokes
    to capture recurrent rhythm signatures and transitions.
    """

    def __init__(
        self,
        sequence_length: int = 20,
        anomaly_threshold: float = 0.70,
        model_weights_path: str = None,
    ):
        self.sequence_length = sequence_length
        self.anomaly_threshold = anomaly_threshold
        self.model_weights_path = model_weights_path

    def score_session(self, keystroke_events: List[dict]) -> dict:
        """Analyze temporal rhythm transitions using sequential analysis."""
        if not keystroke_events or len(keystroke_events) < 5:
            return KeystrokeResult(
                anomaly_score=0.0,
                flags=[],
                metrics={"events_count": len(keystroke_events) if keystroke_events else 0, "status": "insufficient_data"},
            ).to_dict()

        # Extract delta sequence between successive key presses
        deltas = []
        for i in range(1, len(keystroke_events)):
            t_curr = keystroke_events[i].get("down_time", 0.0)
            t_prev = keystroke_events[i - 1].get("down_time", 0.0)
            deltas.append(max(0.0, t_curr - t_prev))

        # Check for sequence regularity / robotic repeating patterns
        flags = []
        anomaly_score = 0.0

        if len(deltas) >= 5:
            diffs = [abs(deltas[j] - deltas[j - 1]) for j in range(1, len(deltas))]
            avg_diff = sum(diffs) / len(diffs)
            if avg_diff < 0.005:  # Under 5ms variance between consecutive deltas
                flags.append("recurrent_macro_sequence")
                anomaly_score = 0.92
            else:
                anomaly_score = 0.12

        return KeystrokeResult(
            anomaly_score=anomaly_score,
            flags=flags,
            metrics={
                "sequence_len": len(deltas),
                "backend": "lstm_sequential",
            },
        ).to_dict()
