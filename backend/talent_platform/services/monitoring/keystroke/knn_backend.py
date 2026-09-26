"""k-Nearest Neighbors (kNN) anomaly classifier for keystroke dynamics."""

import logging
import math
from typing import Any, Dict, List
from ..base import KeystrokeAnalyzer, KeystrokeResult

logger = logging.getLogger(__name__)

# Check if optional ML libraries are available
try:
    import numpy as np
    from sklearn.neighbors import NearestNeighbors
    SKLEARN_AVAILABLE = True
except ImportError:
    np = None
    NearestNeighbors = None
    SKLEARN_AVAILABLE = False


class KNNKeystrokeAnalyzer(KeystrokeAnalyzer):
    """Keystroke dynamics analyzer using kNN distance / statistical distribution scoring.

    Extracts dwell times (key hold duration) and flight times (inter-key latency)
    to detect synthetic macro typing, clipboard injections, and sudden user swaps.
    """

    def __init__(
        self,
        anomaly_threshold: float = 0.65,
        min_events_required: int = 5,
        baseline_dwell_ms: float = 95.0,
        baseline_flight_ms: float = 140.0,
    ):
        self.anomaly_threshold = anomaly_threshold
        self.min_events_required = min_events_required
        self.baseline_dwell_ms = baseline_dwell_ms
        self.baseline_flight_ms = baseline_flight_ms

        self._knn_model = None
        if SKLEARN_AVAILABLE:
            self._init_sklearn_baseline()

    def _init_sklearn_baseline(self):
        """Initialize synthetic human baseline distribution in scikit-learn."""
        try:
            # Generate synthetic cluster of normal human typing profiles
            # Features: [avg_dwell, std_dwell, avg_flight, std_flight]
            rng = np.random.default_rng(seed=42)
            normal_dwell = rng.normal(loc=self.baseline_dwell_ms, scale=18.0, size=(100, 1))
            normal_dwell_std = rng.normal(loc=25.0, scale=6.0, size=(100, 1))
            normal_flight = rng.normal(loc=self.baseline_flight_ms, scale=35.0, size=(100, 1))
            normal_flight_std = rng.normal(loc=45.0, scale=12.0, size=(100, 1))

            baseline_data = np.hstack([normal_dwell, normal_dwell_std, normal_flight, normal_flight_std])
            # Clip negative values
            baseline_data = np.clip(baseline_data, a_min=10.0, a_max=None)

            self._knn_model = NearestNeighbors(n_neighbors=5, metric="euclidean")
            self._knn_model.fit(baseline_data)
        except Exception as e:
            logger.warning("Failed to initialize sklearn kNN baseline: %s", e)
            self._knn_model = None

    def score_session(self, keystroke_events: List[dict]) -> dict:
        """Analyze keystroke events and return anomaly score with detection flags."""
        if not keystroke_events or len(keystroke_events) < self.min_events_required:
            return KeystrokeResult(
                anomaly_score=0.0,
                flags=[],
                metrics={"events_count": len(keystroke_events) if keystroke_events else 0, "status": "insufficient_data"},
            ).to_dict()

        dwell_times_ms: List[float] = []
        flight_times_ms: List[float] = []

        # Determine if timestamps are in seconds or milliseconds
        # Average human key dwell is ~50-150ms. If raw difference is < 2.0, units are seconds.
        sample_diffs = []
        for evt in keystroke_events[:10]:
            d = float(evt.get("down_time") or evt.get("downTime") or 0.0)
            u = float(evt.get("up_time") or evt.get("upTime") or d)
            if u > d:
                sample_diffs.append(u - d)

        is_seconds = bool(sample_diffs and (sum(sample_diffs) / len(sample_diffs)) < 2.0)
        scale = 1000.0 if is_seconds else 1.0

        prev_up_time = None
        for evt in keystroke_events:
            down = float(evt.get("down_time") or evt.get("downTime") or 0.0) * scale
            up = float(evt.get("up_time") or evt.get("upTime") or (down / scale)) * scale

            dwell = max(0.0, up - down)
            dwell_times_ms.append(dwell)

            if prev_up_time is not None:
                flight = down - prev_up_time
                flight_times_ms.append(flight)
            prev_up_time = up

        if not dwell_times_ms:
            return KeystrokeResult(anomaly_score=0.0, flags=[]).to_dict()

        # Compute statistical descriptors
        avg_dwell = sum(dwell_times_ms) / len(dwell_times_ms)
        var_dwell = sum((x - avg_dwell) ** 2 for x in dwell_times_ms) / len(dwell_times_ms)
        std_dwell = math.sqrt(var_dwell)

        if flight_times_ms:
            avg_flight = sum(flight_times_ms) / len(flight_times_ms)
            var_flight = sum((x - avg_flight) ** 2 for x in flight_times_ms) / len(flight_times_ms)
            std_flight = math.sqrt(var_flight)
        else:
            avg_flight = self.baseline_flight_ms
            std_flight = 25.0

        flags: List[str] = []
        anomaly_score = 0.0

        # Heuristic 1: Robotic Cadence (near-zero variation indicates automated script)
        if len(dwell_times_ms) >= 10 and (std_dwell < 3.5 or std_flight < 4.0):
            flags.append("robotic_cadence")
            anomaly_score = max(anomaly_score, 0.85)

        # Heuristic 2: Clipboard Injection / Superhuman Speed
        fast_flights = [f for f in flight_times_ms if f < 10.0]
        if len(flight_times_ms) > 0 and (len(fast_flights) / len(flight_times_ms) > 0.40):
            flags.append("clipboard_injection")
            anomaly_score = max(anomaly_score, 0.90)

        # Heuristic 3: Ultra-short dwell times (macros)
        if avg_dwell < 18.0:
            flags.append("abnormal_dwell_duration")
            anomaly_score = max(anomaly_score, 0.75)

        # Heuristic 4: Long abnormal pauses (> 20 seconds during continuous prompt)
        long_pauses = [f for f in flight_times_ms if f > 20000.0]
        if len(long_pauses) >= 2:
            flags.append("irregular_long_pauses")
            anomaly_score = max(anomaly_score, 0.45)

        # Compute kNN distance anomaly score if no hard heuristics triggered
        if anomaly_score < self.anomaly_threshold:
            if SKLEARN_AVAILABLE and self._knn_model is not None:
                feature_vec = np.array([[avg_dwell, std_dwell, avg_flight, std_flight]])
                distances, _ = self._knn_model.kneighbors(feature_vec)
                mean_dist = float(distances.mean())
                # Normalize euclidean distance to [0, 1] range (50.0 is typical normal distance)
                knn_score = min(1.0, mean_dist / 160.0)
                anomaly_score = max(anomaly_score, knn_score)
            else:
                # Statistical Z-score fallback distance
                z_dwell = abs(avg_dwell - self.baseline_dwell_ms) / 30.0
                z_flight = abs(avg_flight - self.baseline_flight_ms) / 60.0
                stat_score = min(1.0, (z_dwell + z_flight) / 5.0)
                anomaly_score = max(anomaly_score, stat_score)

        # Estimated typing speed (WPM = (chars/min) / 5)
        total_time_ms = sum(dwell_times_ms) + sum(max(0.0, f) for f in flight_times_ms)
        total_time_min = max(0.001, total_time_ms / 60000.0)
        wpm_est = round((len(dwell_times_ms) / 5.0) / total_time_min, 1)

        metrics = {
            "avg_dwell_ms": round(avg_dwell, 1),
            "std_dwell_ms": round(std_dwell, 1),
            "avg_flight_ms": round(avg_flight, 1),
            "std_flight_ms": round(std_flight, 1),
            "wpm_estimate": wpm_est,
            "events_count": len(keystroke_events),
            "backend": "knn_classifier",
        }

        return KeystrokeResult(
            anomaly_score=anomaly_score,
            flags=flags,
            metrics=metrics,
        ).to_dict()
