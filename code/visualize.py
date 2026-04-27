"""Rendering helpers — drawing lane overlays, bounding boxes, motion
vectors and violation banners onto a frame for qualitative inspection
and for figures in the paper."""

from __future__ import annotations

import cv2
import numpy as np

from detector import Detection
from lane_config import Lane
from vector_analyzer import MotionVector
from violation_detector import TrackState


STATE_COLORS: dict[TrackState, tuple[int, int, int]] = {
    TrackState.NORMAL:    (0, 200, 0),      # green
    TrackState.OPPOSING:  (0, 200, 255),    # amber
    TrackState.VIOLATING: (0, 0, 255),      # red
}


def draw_lanes(frame: np.ndarray, lanes: list[Lane]) -> None:
    overlay = frame.copy()
    for lane in lanes:
        pts = lane.polygon.astype(np.int32)
        cv2.fillPoly(overlay, [pts], (60, 60, 60))
        cv2.polylines(frame, [pts], isClosed=True, color=(200, 200, 200), thickness=1)
        # reference-direction arrow drawn from the polygon centroid
        cx, cy = pts.mean(axis=0).astype(int)
        dx, dy = (lane.reference_vector * 60).astype(int)
        cv2.arrowedLine(
            frame, (int(cx), int(cy)), (int(cx + dx), int(cy + dy)),
            color=(255, 255, 255), thickness=2, tipLength=0.3,
        )
        cv2.putText(
            frame, lane.name, (int(cx) - 30, int(cy) - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA,
        )
    cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, dst=frame)


def draw_detection(
    frame: np.ndarray,
    det: Detection,
    state: TrackState,
    motion: MotionVector | None,
) -> None:
    color = STATE_COLORS.get(state, (255, 255, 255))
    x1, y1, x2, y2 = (int(v) for v in det.bbox_xyxy)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    label = f"#{det.track_id} {det.class_name} {det.confidence:.2f}"
    if state == TrackState.VIOLATING:
        label += " [WRONG-WAY]"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
    cv2.putText(
        frame, label, (x1 + 2, y1 - 4),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA,
    )

    if motion is not None:
        ox, oy = motion.origin
        dx, dy = motion.vector
        norm = float(np.linalg.norm(motion.vector))
        if norm > 1e-6:
            scale = 40.0 / norm
            tip = (int(ox + dx * scale), int(oy + dy * scale))
            cv2.arrowedLine(frame, (int(ox), int(oy)), tip, color, 2, tipLength=0.25)
