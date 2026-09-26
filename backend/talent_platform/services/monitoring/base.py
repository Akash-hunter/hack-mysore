"""Abstract base interfaces and data structures for pluggable monitoring backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GazeResult:
    """Standardized output from any gaze tracking backend."""
    gaze_x: float
    gaze_y: float
    confidence: float
    off_screen: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "gaze_x": round(self.gaze_x, 4),
            "gaze_y": round(self.gaze_y, 4),
            "confidence": round(self.confidence, 4),
            "off_screen": bool(self.off_screen),
        }
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class KeystrokeResult:
    """Standardized output from any keystroke dynamics backend."""
    anomaly_score: float
    flags: List[str]
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "anomaly_score": round(self.anomaly_score, 4),
            "flags": list(self.flags),
        }
        if self.metrics:
            result["metrics"] = self.metrics
        return result


class GazeTracker(ABC):
    """Abstract interface that every gaze tracking plugin must implement."""

    @abstractmethod
    def process_frame(self, frame_bytes: bytes) -> dict:
        """Process a single image frame (bytes from JPEG, PNG, or raw stream).

        Returns:
            dict: {
                'gaze_x': float (-1.0 to 1.0 or screen coordinates),
                'gaze_y': float (-1.0 to 1.0 or screen coordinates),
                'confidence': float (0.0 to 1.0),
                'off_screen': bool,
                ...
            }
        """
        pass


class KeystrokeAnalyzer(ABC):
    """Abstract interface that every keystroke dynamics plugin must implement."""

    @abstractmethod
    def score_session(self, keystroke_events: List[dict]) -> dict:
        """Analyze a sequence of keystroke timing events.

        Args:
            keystroke_events: List of event dicts, each typically containing:
                - key: str (e.g. 'a', 'Backspace', 'Enter')
                - down_time: float (timestamp in seconds or ms)
                - up_time: float (timestamp in seconds or ms)

        Returns:
            dict: {
                'anomaly_score': float (0.0 to 1.0, higher = more suspicious),
                'flags': list[str] (e.g. ['robotic_cadence', 'clipboard_burst']),
                ...
            }
        """
        pass
