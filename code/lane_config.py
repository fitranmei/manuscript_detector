"""Lane region-of-interest + reference direction definitions.

Each lane is a closed polygon in image coordinates together with a
reference unit vector that represents the legally allowed direction of
travel inside that polygon. Image coordinates grow downwards, so a
vector (0, 1) means "from top of frame toward bottom" and (1, 0) means
"left to right" on screen.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Lane:
    name: str
    polygon: np.ndarray          # shape (N, 2), float32
    reference_vector: np.ndarray # shape (2,),   unit vector

    def contains(self, point: tuple[float, float]) -> bool:
        return _point_in_polygon(point, self.polygon)


def _point_in_polygon(point: tuple[float, float], polygon: np.ndarray) -> bool:
    """Ray-casting test; polygon is (N, 2)."""
    x, y = point
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersect = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
        )
        if intersect:
            inside = not inside
        j = i
    return inside


def _unit(vec: tuple[float, float]) -> np.ndarray:
    v = np.asarray(vec, dtype=np.float32)
    n = np.linalg.norm(v)
    if n < 1e-9:
        raise ValueError("Reference vector must be non-zero")
    return v / n


def load_lanes(path: str | Path) -> list[Lane]:
    """Load lanes from a JSON file.

    Expected schema:
        {
          "lanes": [
            {
              "name": "lane_south_bound",
              "polygon": [[x1, y1], [x2, y2], ...],
              "reference_vector": [dx, dy]
            },
            ...
          ]
        }
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    lanes: list[Lane] = []
    for entry in data["lanes"]:
        lanes.append(
            Lane(
                name=entry["name"],
                polygon=np.asarray(entry["polygon"], dtype=np.float32),
                reference_vector=_unit(tuple(entry["reference_vector"])),
            )
        )
    if not lanes:
        raise ValueError(f"No lanes defined in {path}")
    return lanes


def lane_for_point(lanes: list[Lane], point: tuple[float, float]) -> Lane | None:
    for lane in lanes:
        if lane.contains(point):
            return lane
    return None


def angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
    """Return the unsigned angle in degrees between v1 and v2, in [0, 180]."""
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    cos = float(np.dot(v1, v2) / (n1 * n2))
    cos = max(-1.0, min(1.0, cos))
    return math.degrees(math.acos(cos))
