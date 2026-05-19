"""Deadlift form analysis rules."""
from typing import Dict, Any
from app.pose_estimator.base import PoseEstimator


class DeadliftRule:
    """Deadlift form analysis rules."""

    def __init__(self, estimator: PoseEstimator):
        """
        Initialize deadlift rule.

        Args:
            estimator: Pose estimator instance
        """
        self.estimator = estimator

    async def analyze(self, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze deadlift form.

        Checks:
        - Back neutrality (no rounding)
        - Hip hinge pattern
        - Bar path (vertical)
        - Knee tracking (not too far forward)
        - Starting position

        Args:
            pose_data: Pose estimation data

        Returns:
            Analysis result with score and issues
        """
        issues = []
        score = 10.0

        keypoints = pose_data.get("keypoints", {})

        # Check back neutrality
        back_rounding = self._check_back_rounding(keypoints)
        if back_rounding:
            issues.append({
                "type": "back_rounding",
                "severity": "high",
                "description": "Lower back is rounding",
                "correction": "Maintain neutral spine, engage lats, chest up"
            })
            score -= 3.5

        # Check hip hinge
        hip_hinge_issue = self._check_hip_hinge(keypoints)
        if hip_hinge_issue:
            issues.append({
                "type": "poor_hip_hinge",
                "severity": "high",
                "description": "Not using proper hip hinge pattern",
                "correction": "Push hips back, keep shins vertical"
            })
            score -= 3.0

        # Check knee tracking
        knee_issue = self._check_knee_position(keypoints)
        if knee_issue:
            issues.append({
                "type": "knees_too_forward",
                "severity": "medium",
                "description": "Knees are too far forward",
                "correction": "Keep knees behind toes, push hips back more"
            })
            score -= 2.0

        # Check shoulder position
        shoulder_issue = self._check_shoulder_position(keypoints)
        if shoulder_issue:
            issues.append({
                "type": "shoulders_ahead",
                "severity": "medium",
                "description": "Shoulders ahead of bar",
                "correction": "Pull shoulders back, keep bar close to body"
            })
            score -= 2.0

        # Check bar path (if visible - using wrist position as proxy)
        bar_path_issue = self._check_bar_path(keypoints)
        if bar_path_issue:
            issues.append({
                "type": "bar_path_forward",
                "severity": "low",
                "description": "Bar drifting away from body",
                "correction": "Keep bar close, pull back into legs"
            })
            score -= 1.5

        return {
            "exercise": "deadlift",
            "score": max(0.0, score),
            "issues": issues,
            "is_good_form": score >= 8.0,
            "keypoints_analyzed": len(keypoints)
        }

    def _check_back_rounding(self, keypoints: Dict) -> bool:
        """Check if back is rounding (lumbar or thoracic)."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})

        if not all([left_shoulder, left_hip, left_knee]):
            return False

        # Calculate back angle
        angle = self.estimator.calculate_angle(
            left_shoulder,
            left_hip,
            left_knee
        )

        # In good deadlift setup, back angle should be relatively straight
        # If angle is too acute or obtuse, back may be rounding
        return angle < 60 or angle > 120

    def _check_hip_hinge(self, keypoints: Dict) -> bool:
        """Check if proper hip hinge pattern is used."""
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})
        left_ankle = keypoints.get("left_ankle", {})

        if not all([left_hip, left_knee, left_ankle]):
            return False

        # Calculate hip-knee-ankle angle
        angle = self.estimator.calculate_angle(
            left_hip,
            left_knee,
            left_ankle
        )

        # In proper hip hinge, knee angle should be relatively open (>140 degrees)
        # If too bent, it's more of a squat pattern
        return angle < 140

    def _check_knee_position(self, keypoints: Dict) -> bool:
        """Check if knees are too far forward."""
        left_knee = keypoints.get("left_knee", {})
        left_ankle = keypoints.get("left_ankle", {})
        left_wrist = keypoints.get("left_wrist", {})

        if not all([left_knee, left_ankle, left_wrist]):
            return False

        knee_x = left_knee.get("x", 0)
        ankle_x = left_ankle.get("x", 0)
        wrist_x = left_wrist.get("x", 0)  # Proxy for bar position

        # Knees should not extend far beyond bar position
        # In good deadlift, shins should be relatively vertical
        knee_forward = abs(knee_x - ankle_x)

        return knee_forward > 0.1

    def _check_shoulder_position(self, keypoints: Dict) -> bool:
        """Check if shoulders are positioned correctly over bar."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_wrist = keypoints.get("left_wrist", {})

        if not left_shoulder or not left_wrist:
            return False

        shoulder_x = left_shoulder.get("x", 0)
        wrist_x = left_wrist.get("x", 0)

        # Shoulders should be slightly ahead of bar at start
        # But not too far ahead
        distance = shoulder_x - wrist_x

        # If shoulders are too far ahead, it's suboptimal
        return distance > 0.15 or distance < -0.05

    def _check_bar_path(self, keypoints: Dict) -> bool:
        """Check if bar path is vertical (using wrist as proxy)."""
        left_wrist = keypoints.get("left_wrist", {})
        left_ankle = keypoints.get("left_ankle", {})

        if not left_wrist or not left_ankle:
            return False

        wrist_x = left_wrist.get("x", 0)
        ankle_x = left_ankle.get("x", 0)

        # Bar should travel relatively vertical
        # Check if wrist (bar) is too far from ankle (midfoot)
        distance = abs(wrist_x - ankle_x)

        return distance > 0.12
