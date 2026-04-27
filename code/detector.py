"""YOLO26 detector wrapper with integrated BoT-SORT / ByteTrack tracking.

Thin adapter around ultralytics.YOLO so the rest of the pipeline is
decoupled from the inference backend. The wrapper consumes a BGR frame
(OpenCV) and returns a list of Detection objects that already carry a
persistent track_id from the built-in tracker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from ultralytics import YOLO


# COCO vehicle class IDs are identical in YOLO26 / YOLO11 / YOLOv8.
# Source: ultralytics/cfg/datasets/coco.yaml
VEHICLE_CLASS_IDS: dict[int, str] = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


@dataclass
class Detection:
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]

    @property
    def centroid(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox_xyxy
        return ((x1 + x2) * 0.5, (y1 + y2) * 0.5)

    @property
    def bottom_center(self) -> tuple[float, float]:
        """Foot point — more stable than geometric centroid for ground-plane motion."""
        x1, _, x2, y2 = self.bbox_xyxy
        return ((x1 + x2) * 0.5, y2)


class VehicleDetector:
    def __init__(
        self,
        weights: str = "yolo26n.pt",
        tracker_cfg: str = "bytetrack.yaml",
        conf_threshold: float = 0.35,
        iou_threshold: float = 0.5,
        device: str | int | None = None,
        imgsz: int = 640,
        classes: Iterable[int] | None = None,
    ) -> None:
        self.model = YOLO(weights)
        self.tracker_cfg = tracker_cfg
        self.conf = conf_threshold
        self.iou = iou_threshold
        self.device = device
        self.imgsz = imgsz
        self.classes = list(classes) if classes is not None else list(VEHICLE_CLASS_IDS.keys())

    def __call__(self, frame: np.ndarray) -> list[Detection]:
        results = self.model.track(
            source=frame,
            persist=True,
            tracker=self.tracker_cfg,
            conf=self.conf,
            iou=self.iou,
            classes=self.classes,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )
        if not results:
            return []

        r = results[0]
        if r.boxes is None or r.boxes.id is None:
            # No tracked objects in this frame (either nothing detected, or
            # the tracker hasn't assigned IDs yet).
            return []

        xyxy = r.boxes.xyxy.cpu().numpy()
        cls = r.boxes.cls.cpu().numpy().astype(int)
        conf = r.boxes.conf.cpu().numpy()
        ids = r.boxes.id.cpu().numpy().astype(int)

        detections: list[Detection] = []
        for box, c, p, tid in zip(xyxy, cls, conf, ids):
            detections.append(
                Detection(
                    track_id=int(tid),
                    class_id=int(c),
                    class_name=VEHICLE_CLASS_IDS.get(int(c), str(c)),
                    confidence=float(p),
                    bbox_xyxy=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                )
            )
        return detections
