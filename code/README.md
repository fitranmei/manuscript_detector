# Wrong-Way Detection — Experimental Model

Reference implementation for the manuscript
**"Sistem Deteksi Pelanggaran Lawan Arah Kendaraan Menggunakan YOLO26 dan Analisis Vektor Pergerakan Berbasis Tracking Objek."**

## Pipeline

```
video frame ──► YOLO26 (.track) ──► per-frame detections + persistent track IDs
                        │
                        ▼
             MotionVectorAnalyzer
             (smoothed centroid displacement
              over a sliding window)
                        │
                        ▼
           lane polygon lookup ──► Lane reference vector
                        │
                        ▼
             ViolationDetector
             (angle(v_motion, v_ref) ≥ threshold
              sustained ≥ min_duration_frames → flag)
                        │
                        ▼
              annotated video + CSV log
```

## Setup

```
python -m pip install -r requirements.txt
```

The first run downloads the YOLO26 weights automatically
(`yolo26n.pt`, ~5 MB) from Ultralytics.

## Quick start

### 1. Calibrate lanes for your camera

```
python calibrate_lanes.py \
    --video path/to/traffic.mp4 \
    --out ../config/lane_config.json
```

Click polygon corners → press `n` → click the tail and head of the
allowed-direction arrow → press Enter → type a lane name. Repeat for
every lane, then press `s` to save.

### 2. Run the pipeline

```
python main.py \
    --video path/to/traffic.mp4 \
    --lanes ../config/lane_config.json \
    --weights yolo26n.pt \
    --out  annotated.mp4 \
    --log  violations.csv
```

### 3. Evaluate against ground truth

```
python evaluate.py --gt gt.csv --pred violations.csv --tolerance 30
```

## Key hyperparameters

| Flag                | Default | Meaning                                                   |
|---------------------|---------|-----------------------------------------------------------|
| `--conf`            | 0.35    | YOLO26 confidence threshold                               |
| `--angle`           | 135.0   | Degrees above which motion is "opposing" the lane        |
| `--min-duration`    | 15      | Consecutive opposing frames required to flag a violation |
| `--window`          | 10      | Motion-vector smoothing window (frames)                   |

At 25 FPS the defaults mean: a vehicle must travel **against** the lane
direction (within a ±45° cone) for at least **0.6 s** before it is
flagged. This suppresses spurious flags from parked cars, legal turns,
and short tracking glitches.

## Tests

```
python -m pytest tests/ -q
```

Unit tests cover angle math, polygon-in-point, motion-vector smoothing,
and the violation state machine's hysteresis behaviour.
