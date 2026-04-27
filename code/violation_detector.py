"""Wrong-way violation state machine.

A vehicle is flagged as committing a wrong-way violation only when its
motion vector has been opposing the lane's reference direction for at
least `min_duration_frames` consecutive frames. This hysteresis is
what prevents false positives from vehicles that momentarily back up,
make a legal turn, or are briefly mis-tracked.

The rule:
    angle(v_motion, v_reference) > angle_threshold_deg  → opposing
    sustained for ≥ min_duration_frames                 → VIOLATION
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from lane_config import Lane, angle_between


class TrackState(Enum):
    NORMAL = "normal"
    OPPOSING = "opposing"   # angle exceeds threshold, accumulating evidence
    VIOLATING = "violating" # sustained opposition → officially flagged


@dataclass
class ViolationEvent:
    track_id: int
    lane_name: str
    angle_deg: float
    opposing_frames: int
    first_frame_idx: int
    flagged_frame_idx: int


@dataclass
class _TrackState:
    state: TrackState = TrackState.NORMAL
    opposing_streak: int = 0
    opposing_start_frame: int | None = None
    last_angle_deg: float = 0.0
    assigned_lane: str | None = None
    already_reported: bool = False


class ViolationDetector:
    def __init__(
        self,
        angle_threshold_deg: float = 135.0,
        min_duration_frames: int = 15,
        reset_tolerance_frames: int = 3,
    ) -> None:
        """
        Args:
            angle_threshold_deg:
                Angle between motion vector and reference direction above
                which the motion is considered opposing. 135° means the
                vector points "backwards" with a ±45° cone of tolerance.
            min_duration_frames:
                Number of consecutive opposing frames required to promote
                state to VIOLATING. At 25 FPS, 15 frames = 0.6 s.
            reset_tolerance_frames:
                How many non-opposing frames to tolerate before the
                opposing streak is cleared. Small value → strict; larger
                value → tolerant of brief detection noise.
        """
        self.angle_threshold_deg = angle_threshold_deg
        self.min_duration_frames = min_duration_frames
        self.reset_tolerance_frames = reset_tolerance_frames
        self._states: dict[int, _TrackState] = {}
        self._forgiveness: dict[int, int] = {}

    def update(
        self,
        track_id: int,
        frame_idx: int,
        motion_vector: np.ndarray,
        lane: Lane,
    ) -> tuple[TrackState, ViolationEvent | None]:
        angle = angle_between(motion_vector, lane.reference_vector)
        st = self._states.setdefault(track_id, _TrackState(assigned_lane=lane.name))
        st.last_angle_deg = angle
        st.assigned_lane = lane.name

        if angle >= self.angle_threshold_deg:
            # Opposing frame
            self._forgiveness[track_id] = 0
            if st.opposing_streak == 0:
                st.opposing_start_frame = frame_idx
            st.opposing_streak += 1

            if st.opposing_streak >= self.min_duration_frames and st.state != TrackState.VIOLATING:
                st.state = TrackState.VIOLATING
                if not st.already_reported:
                    st.already_reported = True
                    first = st.opposing_start_frame if st.opposing_start_frame is not None else frame_idx
                    event = ViolationEvent(
                        track_id=track_id,
                        lane_name=lane.name,
                        angle_deg=angle,
                        opposing_frames=st.opposing_streak,
                        first_frame_idx=first,
                        flagged_frame_idx=frame_idx,
                    )
                    return st.state, event
            elif st.state == TrackState.NORMAL:
                st.state = TrackState.OPPOSING
        else:
            # Non-opposing frame — decay streak after a tolerance window
            miss = self._forgiveness.get(track_id, 0) + 1
            self._forgiveness[track_id] = miss
            if miss > self.reset_tolerance_frames:
                st.opposing_streak = 0
                st.opposing_start_frame = None
                if st.state == TrackState.OPPOSING:
                    st.state = TrackState.NORMAL
                # A track that already VIOLATED stays flagged until it
                # leaves the frame (drop()), so a reformed driver who
                # turns around mid-violation is not un-flagged.

        return st.state, None

    def state_of(self, track_id: int) -> TrackState:
        st = self._states.get(track_id)
        return st.state if st else TrackState.NORMAL

    def drop(self, track_id: int) -> None:
        self._states.pop(track_id, None)
        self._forgiveness.pop(track_id, None)
