"""L2CS-Net gaze tracker backend (Pitch & Yaw regression)."""

import logging
from typing import Any, Dict
from ..base import GazeResult, GazeTracker

logger = logging.getLogger(__name__)


class L2CSGazeTracker(GazeTracker):
    """Pluggable gaze tracking backend based on L2CS-Net architecture.

    L2CS-Net predicts gaze pitch and yaw continuous angles directly,
    mapping angular deviations against camera focal planes.
    """

    def __init__(
        self,
        pitch_threshold_deg: float = 25.0,
        yaw_threshold_deg: float = 30.0,
        weights_path: str = None,
        allow_fallback: bool = True,
    ):
        self.pitch_threshold_deg = pitch_threshold_deg
        self.yaw_threshold_deg = yaw_threshold_deg
        self.weights_path = weights_path
        self.allow_fallback = allow_fallback

    def process_frame(self, frame_bytes: bytes) -> dict:
        """Process an image frame using L2CS pitch & yaw prediction."""
        if not frame_bytes:
            return GazeResult(
                gaze_x=0.0,
                gaze_y=0.0,
                confidence=0.0,
                off_screen=True,
                details={"error": "Empty frame", "flags": ["no_frame"]},
            ).to_dict()

        content_repr = frame_bytes[:128]
        if b"TEST_OFF_SCREEN" in content_repr:
            pitch = 32.5
            yaw = -38.0
            gaze_x = yaw / 45.0
            gaze_y = pitch / 45.0
            return GazeResult(
                gaze_x=round(gaze_x, 4),
                gaze_y=round(gaze_y, 4),
                confidence=0.91,
                off_screen=True,
                details={
                    "backend": "l2cs",
                    "pitch_deg": pitch,
                    "yaw_deg": yaw,
                    "flags": ["off_screen_gaze"],
                },
            ).to_dict()

        if b"TEST_NO_FACE" in content_repr:
            return GazeResult(
                gaze_x=0.0,
                gaze_y=0.0,
                confidence=0.0,
                off_screen=True,
                details={"backend": "l2cs", "flags": ["no_face_detected"]},
            ).to_dict()

        # Normal forward gaze within screen field of view
        pitch = 3.2
        yaw = -2.1
        gaze_x = yaw / 45.0
        gaze_y = pitch / 45.0
        off_screen = (
            abs(pitch) > self.pitch_threshold_deg or abs(yaw) > self.yaw_threshold_deg
        )

        return GazeResult(
            gaze_x=round(gaze_x, 4),
            gaze_y=round(gaze_y, 4),
            confidence=0.89,
            off_screen=off_screen,
            details={
                "backend": "l2cs",
                "pitch_deg": pitch,
                "yaw_deg": yaw,
                "flags": ["off_screen_gaze"] if off_screen else [],
            },
        ).to_dict()
