"""Pluggable monitoring backends for gaze tracking and keystroke dynamics.

This package provides interchangeable backends behind standard contracts,
allowing seamless swapping between MediaPipe / L2CS-Net and kNN / LSTM models,
with Nemotron 3.5 Lightning sitting on top as the fast synthesis agent.
"""

from typing import Dict, Type
from .base import GazeResult, GazeTracker, KeystrokeResult, KeystrokeAnalyzer
from .gaze.mediapipe_backend import MediaPipeGazeTracker
from .gaze.l2cs_backend import L2CSGazeTracker
from .keystroke.knn_backend import KNNKeystrokeAnalyzer
from .keystroke.lstm_backend import LSTMKeystrokeAnalyzer
from .nemotron_agent import NemotronMonitoringAgent

# Pluggable backend registries
GAZE_BACKENDS: Dict[str, Type[GazeTracker]] = {
    "mediapipe": MediaPipeGazeTracker,
    "l2cs": L2CSGazeTracker,
}

KEYSTROKE_BACKENDS: Dict[str, Type[KeystrokeAnalyzer]] = {
    "knn": KNNKeystrokeAnalyzer,
    "lstm": LSTMKeystrokeAnalyzer,
}


def register_gaze_backend(name: str, backend_cls: Type[GazeTracker]) -> None:
    """Register a custom gaze tracking plugin backend."""
    if not issubclass(backend_cls, GazeTracker):
        raise TypeError(f"{backend_cls} must subclass GazeTracker")
    GAZE_BACKENDS[name.lower()] = backend_cls


def register_keystroke_backend(name: str, backend_cls: Type[KeystrokeAnalyzer]) -> None:
    """Register a custom keystroke dynamics plugin backend."""
    if not issubclass(backend_cls, KeystrokeAnalyzer):
        raise TypeError(f"{backend_cls} must subclass KeystrokeAnalyzer")
    KEYSTROKE_BACKENDS[name.lower()] = backend_cls


def get_gaze_tracker(name: str = "mediapipe", **kwargs) -> GazeTracker:
    """Instantiate and return a gaze tracker backend by name."""
    key = name.lower()
    if key not in GAZE_BACKENDS:
        raise ValueError(
            f"Unknown gaze backend '{name}'. Available: {list(GAZE_BACKENDS.keys())}"
        )
    return GAZE_BACKENDS[key](**kwargs)


def get_keystroke_analyzer(name: str = "knn", **kwargs) -> KeystrokeAnalyzer:
    """Instantiate and return a keystroke analyzer backend by name."""
    key = name.lower()
    if key not in KEYSTROKE_BACKENDS:
        raise ValueError(
            f"Unknown keystroke backend '{name}'. Available: {list(KEYSTROKE_BACKENDS.keys())}"
        )
    return KEYSTROKE_BACKENDS[key](**kwargs)


__all__ = [
    "GazeTracker",
    "KeystrokeAnalyzer",
    "GazeResult",
    "KeystrokeResult",
    "MediaPipeGazeTracker",
    "L2CSGazeTracker",
    "KNNKeystrokeAnalyzer",
    "LSTMKeystrokeAnalyzer",
    "NemotronMonitoringAgent",
    "GAZE_BACKENDS",
    "KEYSTROKE_BACKENDS",
    "get_gaze_tracker",
    "get_keystroke_analyzer",
    "register_gaze_backend",
    "register_keystroke_backend",
]
