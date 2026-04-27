"""Per-track motion vector estimation from centroid trajectories.

For each track_id we keep a short ring-buffer of recent (frame_idx,
x, y) samples. The motion vector is computed as the displacement
between the oldest and newest samples in the buffer — this gives a
smoothed direction estimate that ignores single-frame jitter from the
detector / tracker.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np


@dataclass
class _TrackHistory:
    points: deque = field(default_factory=lambda: deque(maxlen=16))


@dataclass
class MotionVector:
    track_id: int
    origin: tuple[float, float]   # latest point
    vector: np.ndarray            # shape (2,), image-space displacement
    speed_px_per_frame: float     # magnitude / window_length_in_frames
    frames_observed: int          # number of samples contributing


class MotionVectorAnalyzer:
    def __init__(
        self,
        window: int = 10,
        min_displacement_px: float = 4.0,
    ) -> None:
        """
        Args:
            window:
                Number of past frames used to estimate direction. Larger →
                smoother but laggier. 10 frames at 25 FPS = 0.4 s, a
                reasonable trade-off for urban traffic.
            min_displacement_px:
                Tracks whose accumulated displacement is smaller than this
                are treated as stationary (no motion vector emitted).
        """
        self.window = window
        self.min_displacement_px = min_displacement_px
        self._tracks: dict[int, _TrackHistory] = {}

    def update(self, track_id: int, frame_idx: int, point: tuple[float, float]) -> MotionVector | None:
        history = self._tracks.setdefault(track_id, _TrackHistory(points=deque(maxlen=self.window)))
        history.points.append((frame_idx, float(point[0]), float(point[1])))

        if len(history.points) < 2:
            return None

        f0, x0, y0 = history.points[0]
        f1, x1, y1 = history.points[-1]
        displacement = np.array([x1 - x0, y1 - y0], dtype=np.float32)
        magnitude = float(np.linalg.norm(displacement))

        if magnitude < self.min_displacement_px:
            return None

        frame_span = max(f1 - f0, 1)
        return MotionVector(
            track_id=track_id,
            origin=(x1, y1),
            vector=displacement,
            speed_px_per_frame=magnitude / frame_span,
            frames_observed=len(history.points),
        )

    def drop(self, track_id: int) -> None:
        self._tracks.pop(track_id, None)

    def active_tracks(self) -> set[int]:
        return set(self._tracks.keys())
