"""End-to-end wrong-way detection pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np

from detector import Detection, VehicleDetector
from lane_config import Lane, lane_for_point, load_lanes
from vector_analyzer import MotionVector, MotionVectorAnalyzer
from violation_detector import TrackState, ViolationDetector, ViolationEvent


@dataclass
class FrameResult:
    frame_idx: int
    frame: np.ndarray
    detections: list[Detection]
    motion_vectors: dict[int, MotionVector]
    track_states: dict[int, TrackState]
    new_violations: list[ViolationEvent]


class WrongWayPipeline:
    def __init__(
        self,
        detector: VehicleDetector,
        lanes: list[Lane],
        analyzer: MotionVectorAnalyzer,
        violation: ViolationDetector,
    ) -> None:
        self.detector = detector
        self.lanes = lanes
        self.analyzer = analyzer
        self.violation = violation

    @classmethod
    def from_config(
        cls,
        lane_config_path: str | Path,
        weights: str = "yolo26n.pt",
        tracker_cfg: str = "bytetrack.yaml",
        conf_threshold: float = 0.35,
        angle_threshold_deg: float = 135.0,
        min_duration_frames: int = 15,
        window: int = 10,
        min_displacement_px: float = 4.0,
        device: str | int | None = None,
    ) -> "WrongWayPipeline":
        return cls(
            detector=VehicleDetector(
                weights=weights,
                tracker_cfg=tracker_cfg,
                conf_threshold=conf_threshold,
                device=device,
            ),
            lanes=load_lanes(lane_config_path),
            analyzer=MotionVectorAnalyzer(window=window, min_displacement_px=min_displacement_px),
            violation=ViolationDetector(
                angle_threshold_deg=angle_threshold_deg,
                min_duration_frames=min_duration_frames,
            ),
        )

    def process_frame(self, frame: np.ndarray, frame_idx: int) -> FrameResult:
        detections = self.detector(frame)
        seen_ids: set[int] = set()
        motion_vectors: dict[int, MotionVector] = {}
        track_states: dict[int, TrackState] = {}
        new_violations: list[ViolationEvent] = []

        for det in detections:
            seen_ids.add(det.track_id)
            foot = det.bottom_center
            mv = self.analyzer.update(det.track_id, frame_idx, foot)
            if mv is None:
                track_states[det.track_id] = self.violation.state_of(det.track_id)
                continue
            motion_vectors[det.track_id] = mv

            lane = lane_for_point(self.lanes, foot)
            if lane is None:
                # Outside any monitored lane — still record current state
                track_states[det.track_id] = self.violation.state_of(det.track_id)
                continue

            state, event = self.violation.update(det.track_id, frame_idx, mv.vector, lane)
            track_states[det.track_id] = state
            if event is not None:
                new_violations.append(event)

        # Clean up state for tracks that disappeared from the frame.
        stale = self.analyzer.active_tracks() - seen_ids
        for tid in stale:
            self.analyzer.drop(tid)
            self.violation.drop(tid)

        return FrameResult(
            frame_idx=frame_idx,
            frame=frame,
            detections=detections,
            motion_vectors=motion_vectors,
            track_states=track_states,
            new_violations=new_violations,
        )

    def run_video(self, video_path: str | Path) -> Iterator[FrameResult]:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")
        try:
            frame_idx = 0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                yield self.process_frame(frame, frame_idx)
                frame_idx += 1
        finally:
            cap.release()

    def run_images(
        self,
        image_dir: str | Path,
        extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp"),
    ) -> Iterator[FrameResult]:
        """Feed a sorted folder of images as if they were consecutive video frames.

        Images must be sequential (e.g. extracted from the same video clip)
        because tracking and motion-vector analysis require temporal continuity.
        Files are sorted lexicographically, so zero-padded names work correctly
        (frame_0001.jpg, frame_0002.jpg, …).
        """
        image_dir = Path(image_dir)
        paths = sorted(
            p for p in image_dir.iterdir()
            if p.is_file() and p.suffix.lower() in extensions
        )
        if not paths:
            raise RuntimeError(
                f"No images found in {image_dir} "
                f"(looked for {', '.join(extensions)})"
            )
        for frame_idx, img_path in enumerate(paths):
            frame = cv2.imread(str(img_path))
            if frame is None:
                continue
            yield self.process_frame(frame, frame_idx)
