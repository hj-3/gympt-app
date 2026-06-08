"""Rep counting with angle-based state machine for exercise tracking."""
import math
import logging
from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RepState(str, Enum):
    """Rep counting states."""
    STARTING = "starting"
    DOWN = "down"
    UP = "up"
    COMPLETED = "completed"


@dataclass
class RepCountResult:
    """Result of rep counting."""
    current_reps: int
    total_reps: int
    current_state: RepState
    position_value: float


class RepCounter:
    """
    Angle-based rep counter with state machine.

    Uses joint angles (degrees) instead of pixel distances so counts are
    independent of camera distance or subject size.
    State machine: STARTING → DOWN (angle < down_threshold)
                             → UP   (angle > down+hysteresis)
                             → COMPLETED (angle > up_threshold)
    """

    # Angle-based thresholds (degrees). Small angle = joint is bent (down).
    DEFAULT_THRESHOLDS = {
        "squat": {
            "down_threshold": 100,   # knee angle below this → bottom position
            "up_threshold":   160,   # knee angle above this → fully standing
            "hysteresis":      10,
        },
        "lunge": {
            "down_threshold": 100,
            "up_threshold":   160,
            "hysteresis":      10,
        },
        "pushup": {
            "down_threshold":  90,   # elbow angle below this → chest near floor
            "up_threshold":   150,   # elbow angle above this → arms extended
            "hysteresis":      10,
        },
        "deadlift": {
            "down_threshold": 100,   # hip angle below this → bent over
            "up_threshold":   160,   # hip angle above this → standing
            "hysteresis":      10,
        },
        "plank": {
            "down_threshold": 0,
            "up_threshold":   0,
            "hysteresis":     0,
        },
    }

    def __init__(self, exercise_type: str, thresholds: Optional[Dict] = None):
        self.exercise_type = exercise_type.lower()
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.get(
            self.exercise_type,
            self.DEFAULT_THRESHOLDS["squat"]
        )
        self.current_state = RepState.STARTING
        self.total_reps = 0
        self.previous_position = 0.0
        logger.info(f"RepCounter initialized for {exercise_type} with thresholds: {self.thresholds}")

    @staticmethod
    def _calc_angle(a: Dict, b: Dict, c: Dict) -> float:
        """
        Calculate the angle at joint b formed by points a-b-c (degrees, 0-180).
        Uses 2D (x, y) coordinates which are stable from MediaPipe.
        """
        ax, ay = a.get("x", 0), a.get("y", 0)
        bx, by = b.get("x", 0), b.get("y", 0)
        cx, cy = c.get("x", 0), c.get("y", 0)
        ba = (ax - bx, ay - by)
        bc = (cx - bx, cy - by)
        dot = ba[0] * bc[0] + ba[1] * bc[1]
        mag = math.sqrt(ba[0]**2 + ba[1]**2) * math.sqrt(bc[0]**2 + bc[1]**2)
        if mag < 1e-6:
            return 180.0
        cosine = max(-1.0, min(1.0, dot / mag))
        return math.degrees(math.acos(cosine))

    def count_reps(self, keypoints: Dict[str, Dict[str, float]]) -> RepCountResult:
        position = self._calculate_position(keypoints)
        if position is None:
            logger.warning("Could not calculate position from keypoints")
            return RepCountResult(
                current_reps=self.total_reps,
                total_reps=self.total_reps,
                current_state=self.current_state,
                position_value=0.0
            )

        previous_state = self.current_state
        self._update_state(position)

        if self.current_state == RepState.COMPLETED:
            self.total_reps += 1
            self.current_state = RepState.STARTING
            logger.info(f"Rep completed! Total reps: {self.total_reps}")

        if previous_state != self.current_state:
            logger.debug(
                f"State transition: {previous_state} -> {self.current_state} "
                f"(angle: {position:.1f}°)"
            )

        self.previous_position = position
        return RepCountResult(
            current_reps=self.total_reps,
            total_reps=self.total_reps,
            current_state=self.current_state,
            position_value=position
        )

    def _calculate_position(self, keypoints: Dict) -> Optional[float]:
        if self.exercise_type in ("squat", "lunge"):
            return self._calculate_squat_position(keypoints)
        elif self.exercise_type == "pushup":
            return self._calculate_pushup_position(keypoints)
        elif self.exercise_type == "deadlift":
            return self._calculate_deadlift_position(keypoints)
        elif self.exercise_type == "plank":
            return 0.0
        else:
            logger.warning(f"Unknown exercise type: {self.exercise_type}")
            return None

    def _calculate_squat_position(self, keypoints: Dict) -> Optional[float]:
        """Knee angle at joint (hip-knee-ankle). Smaller = deeper squat."""
        for side in ("left", "right"):
            hip   = keypoints.get(f"{side}_hip")
            knee  = keypoints.get(f"{side}_knee")
            ankle = keypoints.get(f"{side}_ankle")
            if hip and knee and ankle:
                angle = self._calc_angle(hip, knee, ankle)
                # Use average of both sides when both available
                other_side = "right" if side == "left" else "left"
                oh = keypoints.get(f"{other_side}_hip")
                ok = keypoints.get(f"{other_side}_knee")
                oa = keypoints.get(f"{other_side}_ankle")
                if oh and ok and oa:
                    angle = (angle + self._calc_angle(oh, ok, oa)) / 2
                return angle
        return None

    def _calculate_pushup_position(self, keypoints: Dict) -> Optional[float]:
        """Elbow angle (shoulder-elbow-wrist). Smaller = lower position."""
        for side in ("left", "right"):
            shoulder = keypoints.get(f"{side}_shoulder")
            elbow    = keypoints.get(f"{side}_elbow")
            wrist    = keypoints.get(f"{side}_wrist")
            if shoulder and elbow and wrist:
                angle = self._calc_angle(shoulder, elbow, wrist)
                other_side = "right" if side == "left" else "left"
                os = keypoints.get(f"{other_side}_shoulder")
                oe = keypoints.get(f"{other_side}_elbow")
                ow = keypoints.get(f"{other_side}_wrist")
                if os and oe and ow:
                    angle = (angle + self._calc_angle(os, oe, ow)) / 2
                return angle
        return None

    def _calculate_deadlift_position(self, keypoints: Dict) -> Optional[float]:
        """Hip angle (shoulder-hip-knee). Smaller = bent over."""
        for side in ("left", "right"):
            shoulder = keypoints.get(f"{side}_shoulder")
            hip      = keypoints.get(f"{side}_hip")
            knee     = keypoints.get(f"{side}_knee")
            if shoulder and hip and knee:
                return self._calc_angle(shoulder, hip, knee)
        return None

    def _update_state(self, position: float):
        down_thresh = self.thresholds["down_threshold"]
        up_thresh   = self.thresholds["up_threshold"]
        hysteresis  = self.thresholds["hysteresis"]

        if self.current_state == RepState.STARTING:
            if position < down_thresh:
                self.current_state = RepState.DOWN

        elif self.current_state == RepState.DOWN:
            if position > (down_thresh + hysteresis):
                self.current_state = RepState.UP

        elif self.current_state == RepState.UP:
            if position > up_thresh:
                self.current_state = RepState.COMPLETED

    def reset(self):
        self.current_state = RepState.STARTING
        self.total_reps = 0
        self.previous_position = 0.0
        logger.info(f"RepCounter reset for {self.exercise_type}")

    def get_progress(self) -> float:
        if self.current_state == RepState.STARTING:
            return 0.0
        elif self.current_state == RepState.DOWN:
            return 0.33
        elif self.current_state == RepState.UP:
            return 0.66
        elif self.current_state == RepState.COMPLETED:
            return 1.0
        return 0.0
