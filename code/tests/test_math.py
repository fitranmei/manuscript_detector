"""Unit tests for the math-only components of the pipeline.

Run with:  python -m pytest tests/ -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lane_config import Lane, angle_between, lane_for_point
from vector_analyzer import MotionVectorAnalyzer
from violation_detector import TrackState, ViolationDetector


def _lane(name: str, ref: tuple[float, float]) -> Lane:
    poly = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.float32)
    return Lane(name=name, polygon=poly,
                reference_vector=np.asarray(ref, dtype=np.float32) /
                                  float(np.linalg.norm(ref)))


def test_angle_between_orthogonal():
    assert angle_between(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(90.0)


def test_angle_between_opposite():
    assert angle_between(np.array([1.0, 0.0]), np.array([-1.0, 0.0])) == pytest.approx(180.0)


def test_angle_between_same():
    assert angle_between(np.array([1.0, 2.0]), np.array([3.0, 6.0])) == pytest.approx(0.0, abs=1e-4)


def test_lane_for_point_hit_and_miss():
    lane = _lane("test", (1.0, 0.0))
    assert lane_for_point([lane], (50, 50)) is lane
    assert lane_for_point([lane], (-10, 50)) is None


def test_motion_vector_rejects_stationary_track():
    analyzer = MotionVectorAnalyzer(window=5, min_displacement_px=5.0)
    for i in range(5):
        mv = analyzer.update(track_id=1, frame_idx=i, point=(100.0, 100.0))
    assert mv is None  # zero displacement → rejected


def test_motion_vector_captures_direction():
    analyzer = MotionVectorAnalyzer(window=5, min_displacement_px=1.0)
    mv = None
    for i in range(5):
        mv = analyzer.update(track_id=1, frame_idx=i, point=(100.0 + 10 * i, 200.0))
    assert mv is not None
    assert mv.vector[0] > 0 and abs(mv.vector[1]) < 1e-6
    assert mv.speed_px_per_frame == pytest.approx(10.0)


def test_violation_requires_sustained_opposition():
    lane = _lane("test", (0.0, 1.0))  # reference points down
    detector = ViolationDetector(angle_threshold_deg=135.0,
                                 min_duration_frames=5,
                                 reset_tolerance_frames=2)

    # Moving UP (opposite of reference) for 4 frames — not yet flagged
    for i in range(4):
        state, event = detector.update(track_id=1, frame_idx=i,
                                        motion_vector=np.array([0.0, -5.0]),
                                        lane=lane)
        assert event is None
        assert state == TrackState.OPPOSING

    # 5th opposing frame triggers the violation
    state, event = detector.update(track_id=1, frame_idx=4,
                                    motion_vector=np.array([0.0, -5.0]),
                                    lane=lane)
    assert state == TrackState.VIOLATING
    assert event is not None
    assert event.opposing_frames == 5
    assert event.first_frame_idx == 0


def test_violation_not_triggered_by_turning_vehicle():
    lane = _lane("test", (0.0, 1.0))  # reference points down
    detector = ViolationDetector(angle_threshold_deg=135.0,
                                 min_duration_frames=5,
                                 reset_tolerance_frames=2)

    # A vehicle turning right: motion vector 90° from reference → NOT opposing
    for i in range(20):
        state, event = detector.update(track_id=2, frame_idx=i,
                                        motion_vector=np.array([5.0, 0.0]),
                                        lane=lane)
        assert event is None
    assert state == TrackState.NORMAL


def test_brief_opposition_does_not_trigger():
    lane = _lane("test", (0.0, 1.0))
    detector = ViolationDetector(angle_threshold_deg=135.0,
                                 min_duration_frames=10,
                                 reset_tolerance_frames=2)

    # 3 opposing frames then vehicle resumes correct direction
    for i in range(3):
        detector.update(1, i, np.array([0.0, -5.0]), lane)
    for i in range(3, 20):
        state, event = detector.update(1, i, np.array([0.0, 5.0]), lane)
        assert event is None
    assert state == TrackState.NORMAL
