"""Evaluation harness for ground-truthed wrong-way detection.

Reads a CSV of ground-truth violations and a CSV of predicted
violations, then reports precision / recall / F1 and average detection
latency. A prediction matches ground-truth when the track_id is the
same (after optional ID-mapping) and the flagged_frame_idx falls
within a configurable temporal tolerance of the annotated violation
start.

Ground-truth CSV columns: track_id,first_frame,last_frame,lane
Prediction CSV columns:   track_id,first_frame_idx,flagged_frame_idx,lane_name,angle_deg,opposing_frames
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GT:
    track_id: int
    first_frame: int
    last_frame: int
    lane: str


@dataclass
class Pred:
    track_id: int
    first_frame_idx: int
    flagged_frame_idx: int
    lane_name: str


def _read_csv(path: Path, fields: list[str]) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = set(fields) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} missing columns: {sorted(missing)}")
        return list(reader)


def load_gt(path: Path) -> list[GT]:
    rows = _read_csv(path, ["track_id", "first_frame", "last_frame", "lane"])
    return [
        GT(int(r["track_id"]), int(r["first_frame"]), int(r["last_frame"]), r["lane"])
        for r in rows
    ]


def load_preds(path: Path) -> list[Pred]:
    rows = _read_csv(path, ["track_id", "first_frame_idx", "flagged_frame_idx", "lane_name"])
    return [
        Pred(int(r["track_id"]), int(r["first_frame_idx"]), int(r["flagged_frame_idx"]), r["lane_name"])
        for r in rows
    ]


def evaluate(
    gts: list[GT],
    preds: list[Pred],
    tolerance_frames: int = 30,
) -> dict[str, float]:
    matched_gt: set[int] = set()
    matched_pred: set[int] = set()
    latencies: list[int] = []

    for pi, p in enumerate(preds):
        for gi, g in enumerate(gts):
            if gi in matched_gt:
                continue
            if p.track_id != g.track_id or p.lane_name != g.lane:
                continue
            if g.first_frame - tolerance_frames <= p.flagged_frame_idx <= g.last_frame + tolerance_frames:
                matched_gt.add(gi)
                matched_pred.add(pi)
                latencies.append(max(p.flagged_frame_idx - g.first_frame, 0))
                break

    tp = len(matched_pred)
    fp = len(preds) - tp
    fn = len(gts) - len(matched_gt)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    return {
        "tp": float(tp),
        "fp": float(fp),
        "fn": float(fn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "avg_detection_latency_frames": avg_latency,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True, type=Path)
    ap.add_argument("--pred", required=True, type=Path)
    ap.add_argument("--tolerance", type=int, default=30,
                    help="Frame-level tolerance when matching predictions to GT.")
    args = ap.parse_args()

    metrics = evaluate(load_gt(args.gt), load_preds(args.pred), args.tolerance)
    for k, v in metrics.items():
        print(f"{k:>30s}: {v:.4f}")


if __name__ == "__main__":
    main()
