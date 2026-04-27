"""Interactive lane-polygon + reference-direction calibration tool.

Workflow:
    1. Opens the first frame of the given video.
    2. Click to add polygon vertices for a lane. Press 'n' to finish that
       polygon; you are then prompted to click twice to set the reference
       direction arrow (from → to).
    3. Repeat for each lane. Press 's' to save, 'q' to quit without saving.

Usage:
    python calibrate_lanes.py --video traffic.mp4 --out ../config/lane_config.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


class _Calibrator:
    def __init__(self, frame: np.ndarray) -> None:
        self.base = frame
        self.display = frame.copy()
        self.current_polygon: list[tuple[int, int]] = []
        self.arrow_points: list[tuple[int, int]] = []
        self.mode = "polygon"   # or "arrow"
        self.lanes: list[dict] = []

    def on_mouse(self, event: int, x: int, y: int, *_: object) -> None:
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        if self.mode == "polygon":
            self.current_polygon.append((x, y))
        elif self.mode == "arrow":
            self.arrow_points.append((x, y))
        self._redraw()

    def _redraw(self) -> None:
        img = self.base.copy()
        for lane in self.lanes:
            pts = np.asarray(lane["polygon"], dtype=np.int32)
            cv2.polylines(img, [pts], True, (0, 200, 0), 2)
            cx, cy = pts.mean(axis=0).astype(int)
            dx, dy = (np.asarray(lane["reference_vector"]) * 60).astype(int)
            cv2.arrowedLine(img, (cx, cy), (cx + dx, cy + dy), (0, 200, 0), 2, tipLength=0.3)
            cv2.putText(img, lane["name"], (cx - 30, cy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
        if self.current_polygon:
            pts = np.asarray(self.current_polygon, dtype=np.int32)
            cv2.polylines(img, [pts], False, (0, 255, 255), 2)
            for p in self.current_polygon:
                cv2.circle(img, p, 4, (0, 255, 255), -1)
        if len(self.arrow_points) == 2:
            cv2.arrowedLine(img, self.arrow_points[0], self.arrow_points[1],
                            (0, 255, 255), 2, tipLength=0.3)
        cv2.imshow("calibrate", img)

    def finish_polygon(self) -> None:
        if len(self.current_polygon) < 3:
            print("Need at least 3 points.")
            return
        print("Now click twice: first click = arrow tail, second click = arrow head")
        self.mode = "arrow"

    def finish_arrow(self, name: str) -> None:
        if len(self.arrow_points) != 2:
            print("Need exactly 2 arrow clicks.")
            return
        tail, head = self.arrow_points
        dx, dy = head[0] - tail[0], head[1] - tail[1]
        norm = float((dx * dx + dy * dy) ** 0.5) or 1.0
        self.lanes.append({
            "name": name,
            "polygon": [[int(x), int(y)] for x, y in self.current_polygon],
            "reference_vector": [dx / norm, dy / norm],
        })
        self.current_polygon.clear()
        self.arrow_points.clear()
        self.mode = "polygon"
        self._redraw()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, type=Path)
    ap.add_argument("--out",   required=True, type=Path)
    args = ap.parse_args()

    cap = cv2.VideoCapture(str(args.video))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Cannot read first frame from {args.video}")

    cal = _Calibrator(frame)
    cv2.namedWindow("calibrate")
    cv2.setMouseCallback("calibrate", cal.on_mouse)
    cal._redraw()

    print(
        "Keys:\n"
        "  click       add polygon vertex (or arrow endpoint in arrow mode)\n"
        "  n           finish current polygon → switch to arrow mode\n"
        "  Enter       after 2 arrow clicks, confirm and name the lane\n"
        "  z           undo last click\n"
        "  s           save lanes to JSON\n"
        "  q / ESC     quit without saving\n"
    )

    while True:
        key = cv2.waitKey(30) & 0xFF
        if key in (27, ord("q")):
            break
        if key == ord("n") and cal.mode == "polygon":
            cal.finish_polygon()
        if key in (13, 10) and cal.mode == "arrow":   # Enter
            name = input("Lane name: ").strip() or f"lane_{len(cal.lanes)}"
            cal.finish_arrow(name)
        if key == ord("z"):
            if cal.mode == "polygon" and cal.current_polygon:
                cal.current_polygon.pop()
            elif cal.mode == "arrow" and cal.arrow_points:
                cal.arrow_points.pop()
            cal._redraw()
        if key == ord("s"):
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps({"lanes": cal.lanes}, indent=2), encoding="utf-8")
            print(f"Saved {len(cal.lanes)} lanes to {args.out}")
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
