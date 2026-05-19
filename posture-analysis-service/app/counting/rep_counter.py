"""Rep counting with state machine for exercise tracking."""
import logging
from typing import Dict, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RepState(str, Enum):
    """Rep counting states."""
    STARTING = "starting"  # Initial position
    DOWN = "down"          # Bottom of movement
    UP = "up"              # Top of movement
    COMPLETED = "completed" # Rep completed


@dataclass
class RepCountResult:
    """Result of rep counting."""
    current_reps: int
    total_reps: int
    current_state: RepState
    position_value: float  # Current position metric (e.g., hip height)


class RepCounter:
    """
    Rep counter with state machine to prevent double counting.

    Uses hysteresis thresholds to ensure clean state transitions.
    """

    # Default thresholds by exercise type
    DEFAULT_THRESHOLDS = {
        "squat": {
            "down_threshold": 0.15,      # Hip-knee distance for bottom position
            "up_threshold": 0.25,        # Hip-knee distance for top position
            "hysteresis": 0.05,          # Hysteresis buffer (10% of range)
        },
        "pushup": {
            "down_threshold": 0.10,      # Shoulder height for bottom
            "up_threshold": 0.20,        # Shoulder height for top
            "hysteresis": 0.03,
        },
        "plank": {
            # Plank doesn't count reps, it tracks hold time
            "down_threshold": 0.0,
            "up_threshold": 0.0,
            "hysteresis": 0.0,
        },
        "deadlift": {
            "down_threshold": 0.20,
            "up_threshold": 0.35,
            "hysteresis": 0.05,
        }
    }

    def __init__(self, exercise_type: str, thresholds: Optional[Dict] = None):
        """
        Initialize rep counter.

        Args:
            exercise_type: Type of exercise (squat, pushup, etc.)
            thresholds: Optional custom thresholds
        """
        self.exercise_type = exercise_type.lower()
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.get(
            self.exercise_type,
            self.DEFAULT_THRESHOLDS["squat"]
        )

        self.current_state = RepState.STARTING
        self.total_reps = 0
        self.previous_position = 0.0

        logger.info(f"RepCounter initialized for {exercise_type} with thresholds: {self.thresholds}")

    def count_reps(
        self,
        keypoints: Dict[str, Dict[str, float]]
    ) -> RepCountResult:
        """
        Count reps based on keypoint positions.

        Args:
            keypoints: Detected keypoints with coordinates

        Returns:
            RepCountResult with count and state
        """
        # Calculate position metric based on exercise type
        position = self._calculate_position(keypoints)

        if position is None:
            logger.warning("Could not calculate position from keypoints")
            return RepCountResult(
                current_reps=self.total_reps,
                total_reps=self.total_reps,
                current_state=self.current_state,
                position_value=0.0
            )

        # Update state machine
        previous_state = self.current_state
        self._update_state(position)

        # Check if rep completed
        if self.current_state == RepState.COMPLETED:
            self.total_reps += 1
            self.current_state = RepState.STARTING
            logger.info(f"Rep completed! Total reps: {self.total_reps}")

        # Log state transitions
        if previous_state != self.current_state:
            logger.debug(
                f"State transition: {previous_state} -> {self.current_state} "
                f"(position: {position:.3f})"
            )

        self.previous_position = position

        return RepCountResult(
            current_reps=self.total_reps,
            total_reps=self.total_reps,
            current_state=self.current_state,
            position_value=position
        )

    def _calculate_position(self, keypoints: Dict) -> Optional[float]:
        """
        Calculate position metric based on exercise type.

        Returns:
            Position value (normalized 0-1) or None if unable to calculate
        """
        if self.exercise_type == "squat":
            return self._calculate_squat_position(keypoints)
        elif self.exercise_type == "pushup":
            return self._calculate_pushup_position(keypoints)
        elif self.exercise_type == "deadlift":
            return self._calculate_deadlift_position(keypoints)
        elif self.exercise_type == "plank":
            # Plank doesn't use position for rep counting
            return 0.0
        else:
            logger.warning(f"Unknown exercise type: {self.exercise_type}")
            return None

    def _calculate_squat_position(self, keypoints: Dict) -> Optional[float]:
        """Calculate hip-knee vertical distance for squat."""
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})

        if not left_hip or not left_knee:
            return None

        hip_y = left_hip.get("y", 0)
        knee_y = left_knee.get("y", 0)

        # Distance between hip and knee (vertical)
        # When squatting down, hip gets closer to knee
        distance = abs(hip_y - knee_y)

        return distance

    def _calculate_pushup_position(self, keypoints: Dict) -> Optional[float]:
        """Calculate shoulder height for pushup."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_wrist = keypoints.get("left_wrist", {})

        if not left_shoulder or not left_wrist:
            return None

        shoulder_y = left_shoulder.get("y", 0)
        wrist_y = left_wrist.get("y", 0)

        # Vertical distance between shoulder and wrist
        # When lowering, shoulder gets closer to wrist
        distance = abs(shoulder_y - wrist_y)

        return distance

    def _calculate_deadlift_position(self, keypoints: Dict) -> Optional[float]:
        """Calculate hip height for deadlift."""
        left_hip = keypoints.get("left_hip", {})
        left_ankle = keypoints.get("left_ankle", {})

        if not left_hip or not left_ankle:
            return None

        hip_y = left_hip.get("y", 0)
        ankle_y = left_ankle.get("y", 0)

        # Distance from hip to ankle
        # When lifting, hip rises away from ankle
        distance = abs(hip_y - ankle_y)

        return distance

    def _update_state(self, position: float):
        """
        Update state machine based on position.

        Uses hysteresis to prevent false transitions.
        """
        down_thresh = self.thresholds["down_threshold"]
        up_thresh = self.thresholds["up_threshold"]
        hysteresis = self.thresholds["hysteresis"]

        if self.current_state == RepState.STARTING:
            # Transition to DOWN when position drops below threshold
            if position < down_thresh:
                self.current_state = RepState.DOWN

        elif self.current_state == RepState.DOWN:
            # Transition to UP when position rises above threshold + hysteresis
            if position > (down_thresh + hysteresis):
                self.current_state = RepState.UP

        elif self.current_state == RepState.UP:
            # Transition to COMPLETED when reaching top position
            if position > up_thresh:
                self.current_state = RepState.COMPLETED

    def reset(self):
        """Reset rep counter."""
        self.current_state = RepState.STARTING
        self.total_reps = 0
        self.previous_position = 0.0
        logger.info(f"RepCounter reset for {self.exercise_type}")

    def get_progress(self) -> float:
        """
        Get current rep progress (0.0 - 1.0).

        Returns:
            Progress through current rep
        """
        if self.current_state == RepState.STARTING:
            return 0.0
        elif self.current_state == RepState.DOWN:
            return 0.33
        elif self.current_state == RepState.UP:
            return 0.66
        elif self.current_state == RepState.COMPLETED:
            return 1.0
        return 0.0
