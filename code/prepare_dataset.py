"""Download a sample traffic video and extract frames as a dataset.

Usage:
    python prepare_dataset.py
    python prepare_dataset.py --out dataset/frames --every 1 --max-frames 300

The script downloads a publicly available traffic clip from the Ultralytics
assets repository (used by their own documentation examples), then extracts
frames and generates a matching lane_config.json at the correct resolution.

Output layout:
    dataset/
        frames/          ← sequential images (frame_0001.jpg, …)
        lane_config.json ← auto-generated for the video resolution
"""

from __future__ import annotations

import argparse
import json
import shutil
import urllib.request
from pathlib import Path

import cv2


# Ultralytics hosts this clip for their own demo/doc usage.
_VIDEO_URL = "https://ultralytics.com/assets/road.mp4"
_VIDEO_CACHE = Path("dataset") / "_road.mp4"


def download_video(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"[cache] Video already downloaded: {dest}")
        return dest
    print(f"[download] {url}")
    print("           This may take a minute on a slow connection …")
    with urllib.request.urlopen(url) as resp, dest.open("wb") as f:  # noqa: S310
        shutil.copyfileobj(resp, f)
    print(f"[ok] Saved to {dest}")
    return dest


def extract_frames(
    video_path: Path,
    out_dir: Path,
    every: int = 1,
    max_frames: int | None = None,
) -> tuple[int, int, int]:
    """Return (n_frames_saved, width, height)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {video_path}")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[info] Video: {w}×{h}, {total} frames total")

    saved = 0
    idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % every == 0:
                name = out_dir / f"frame_{saved:05d}.jpg"
                cv2.imwrite(str(name), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
                saved += 1
                if max_frames and saved >= max_frames:
                    break
            idx += 1
    finally:
        cap.release()

    print(f"[ok] Extracted {saved} frames → {out_dir}")
    return saved, w, h


def make_lane_config(out_path: Path, w: int, h: int) -> None:
    """Generate a two-lane config scaled to the video resolution.

    The polygons cover the left and right halves of the frame.
    Adjust by re-running calibrate_lanes.py against an actual frame.
    """
    mid = w // 2
    config = {
        "_comment": (
            f"Auto-generated for {w}×{h} resolution. "
            "Run calibrate_lanes.py to adjust polygons to the real scene."
        ),
        "lanes": [
            {
                "name": "lane_southbound",
                "polygon": [
                    [mid, 0], [w, 0], [w, h], [mid, h]
                ],
                "reference_vector": [0.0, 1.0],
            },
            {
                "name": "lane_northbound",
                "polygon": [
                    [0, 0], [mid, 0], [mid, h], [0, h]
                ],
                "reference_vector": [0.0, -1.0],
            },
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"[ok] Lane config → {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare sample traffic dataset.")
    ap.add_argument("--out", type=Path, default=Path("dataset/frames"),
                    help="Output folder for extracted frames.")
    ap.add_argument("--every", type=int, default=1,
                    help="Extract every Nth frame (default: 1 = all frames).")
    ap.add_argument("--max-frames", type=int, default=300,
                    help="Maximum number of frames to extract (default: 300).")
    ap.add_argument("--lane-config", type=Path, default=Path("dataset/lane_config.json"),
                    help="Where to write the auto-generated lane config.")
    ap.add_argument("--url", default=_VIDEO_URL,
                    help="Direct URL to traffic video (mp4).")
    args = ap.parse_args()

    video = download_video(args.url, _VIDEO_CACHE)
    _, w, h = extract_frames(video, args.out, every=args.every, max_frames=args.max_frames)
    make_lane_config(args.lane_config, w, h)

    print()
    print("=" * 60)
    print("Dataset ready. Run the pipeline with:")
    print()
    print(f"  python main.py \\")
    print(f"    --images {args.out} \\")
    print(f"    --lanes  {args.lane_config} \\")
    print(f"    --out    dataset/annotated.mp4 \\")
    print(f"    --log    dataset/violations.csv")
    print()
    print("Tip: re-run calibrate_lanes.py on a real frame for accurate lanes.")
    print("=" * 60)


if __name__ == "__main__":
    main()
