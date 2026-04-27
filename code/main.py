"""CLI entry point: run the wrong-way pipeline on a video file.

Usage:
    python main.py --video traffic.mp4 --lanes ../config/lane_config.json \
                   --weights yolo26n.pt --out annotated.mp4 --log violations.csv
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import cv2

from pipeline import WrongWayPipeline
from visualize import draw_detection, draw_lanes


def main() -> None:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--video",  type=Path, help="Input video file.")
    src.add_argument("--images", type=Path, help="Folder of sequential images (sorted by name).")
    ap.add_argument("--lanes",    required=True, type=Path)
    ap.add_argument("--weights",  default="yolo26n.pt")
    ap.add_argument("--tracker",  default="bytetrack.yaml")
    ap.add_argument("--conf",     type=float, default=0.35)
    ap.add_argument("--angle",    type=float, default=135.0,
                    help="Angle threshold (deg) above which motion is considered opposing.")
    ap.add_argument("--min-duration", type=int, default=15,
                    help="Consecutive opposing frames required to flag a violation.")
    ap.add_argument("--window",   type=int, default=10,
                    help="Motion-vector smoothing window, in frames.")
    ap.add_argument("--device",   default=None,
                    help="CUDA device index or 'cpu'.")
    ap.add_argument("--out",      type=Path, default=None, help="Optional annotated video output.")
    ap.add_argument("--log",      type=Path, default=None, help="Optional CSV of violation events.")
    ap.add_argument("--show",     action="store_true", help="Display frames as they are processed.")
    args = ap.parse_args()

    pipeline = WrongWayPipeline.from_config(
        lane_config_path=args.lanes,
        weights=args.weights,
        tracker_cfg=args.tracker,
        conf_threshold=args.conf,
        angle_threshold_deg=args.angle,
        min_duration_frames=args.min_duration,
        window=args.window,
        device=args.device,
    )

    writer = None
    if args.out is not None:
        if args.video is not None:
            cap_probe = cv2.VideoCapture(str(args.video))
            fps = cap_probe.get(cv2.CAP_PROP_FPS) or 25.0
            w = int(cap_probe.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap_probe.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap_probe.release()
        else:
            # Probe first image for dimensions; assume 25 FPS for image sequences.
            first_img = sorted(args.images.iterdir())[0]
            probe = cv2.imread(str(first_img))
            h, w = probe.shape[:2]
            fps = 25.0
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(args.out), fourcc, fps, (w, h))

    log_fh = None
    log_writer = None
    if args.log is not None:
        log_fh = args.log.open("w", newline="", encoding="utf-8")
        log_writer = csv.writer(log_fh)
        log_writer.writerow([
            "track_id", "lane_name", "first_frame_idx", "flagged_frame_idx",
            "angle_deg", "opposing_frames",
        ])

    total_frames = 0
    total_inference_ms = 0.0
    total_violations = 0
    t0 = time.perf_counter()

    try:
        source_iter = (
            pipeline.run_video(args.video)
            if args.video is not None
            else pipeline.run_images(args.images)
        )
        for result in source_iter:
            total_frames += 1
            total_violations += len(result.new_violations)
            for ev in result.new_violations:
                if log_writer is not None:
                    log_writer.writerow([
                        ev.track_id, ev.lane_name, ev.first_frame_idx,
                        ev.flagged_frame_idx, f"{ev.angle_deg:.2f}", ev.opposing_frames,
                    ])
                print(
                    f"[frame {result.frame_idx}] VIOLATION track={ev.track_id} "
                    f"lane={ev.lane_name} angle={ev.angle_deg:.1f}° "
                    f"duration={ev.opposing_frames} frames"
                )

            draw_lanes(result.frame, pipeline.lanes)
            for det in result.detections:
                state = result.track_states.get(det.track_id)
                motion = result.motion_vectors.get(det.track_id)
                draw_detection(result.frame, det, state, motion)

            if writer is not None:
                writer.write(result.frame)
            if args.show:
                cv2.imshow("wrong-way", result.frame)
                if cv2.waitKey(1) & 0xFF == 27:  # ESC
                    break
    finally:
        if writer is not None:
            writer.release()
        if log_fh is not None:
            log_fh.close()
        if args.show:
            cv2.destroyAllWindows()

    wall = time.perf_counter() - t0
    fps = total_frames / wall if wall > 0 else 0.0
    print(f"\nProcessed {total_frames} frames in {wall:.2f} s ({fps:.1f} FPS)")
    print(f"Flagged {total_violations} wrong-way violations")


if __name__ == "__main__":
    main()
