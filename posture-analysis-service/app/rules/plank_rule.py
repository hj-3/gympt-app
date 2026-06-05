"""Plank form analysis rules."""
from typing import Dict, Any
from app.pose_estimator.base import PoseEstimator


class PlankRule:
    """Plank form analysis rules."""

    def __init__(self, estimator: PoseEstimator):
        """
        Initialize plank rule.

        Args:
            estimator: Pose estimator instance
        """
        self.estimator = estimator

    async def analyze(self, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze plank form.

        Checks:
        - Hip alignment (no sagging or piking)
        - Core engagement (straight line from shoulders to ankles)
        - Shoulder position (directly above elbows)
        - Head/neck alignment

        Args:
            pose_data: Pose estimation data

        Returns:
            Analysis result with score and issues
        """
        issues = []
        score = 10.0

        keypoints = pose_data.get("keypoints", {})

        # Check hip alignment
        hip_sag = self._check_hip_sag(keypoints)
        if hip_sag == "sagging":
            issues.append({
                "type": "hip_sag",
                "severity": "high",
                "description": "엉덩이가 아래로 처지고 있습니다",
                "correction": "코어에 힘을 주고 엉덩이를 어깨 높이에 맞춰 올리세요"
            })
            score -= 3.0
        elif hip_sag == "piking":
            issues.append({
                "type": "hip_pike",
                "severity": "medium",
                "description": "엉덩이가 너무 높습니다",
                "correction": "엉덩이를 낮춰 머리부터 발뒤꿈치까지 일직선을 만드세요"
            })
            score -= 2.0

        # Check shoulder position
        shoulder_issue = self._check_shoulder_position(keypoints)
        if shoulder_issue:
            issues.append({
                "type": "shoulder_misalignment",
                "severity": "medium",
                "description": "어깨가 팔꿈치 위에 정렬되지 않았습니다",
                "correction": "어깨를 팔꿈치 바로 위에 위치시키세요"
            })
            score -= 2.0

        # Check core engagement
        core_issue = self._check_core_engagement(keypoints)
        if core_issue:
            issues.append({
                "type": "poor_core_engagement",
                "severity": "high",
                "description": "코어에 힘이 빠져 있습니다",
                "correction": "복근에 힘을 주고 척추를 중립으로 유지하세요"
            })
            score -= 3.0

        # Check head position
        head_issue = self._check_head_position(keypoints)
        if head_issue:
            issues.append({
                "type": "head_misalignment",
                "severity": "low",
                "description": "머리가 중립 위치에 있지 않습니다",
                "correction": "목을 중립으로 유지하고 시선은 바닥을 향하세요"
            })
            score -= 1.0

        return {
            "exercise": "plank",
            "score": max(0.0, score),
            "issues": issues,
            "is_good_form": score >= 8.0,
            "keypoints_analyzed": len(keypoints)
        }

    def _check_hip_sag(self, keypoints: Dict) -> str:
        """
        Check hip alignment (sagging or piking).

        Returns:
            "good", "sagging", or "piking"
        """
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})
        left_ankle = keypoints.get("left_ankle", {})

        if not all([left_shoulder, left_hip, left_ankle]):
            return "good"

        shoulder_y = left_shoulder.get("y", 0)
        hip_y = left_hip.get("y", 0)
        ankle_y = left_ankle.get("y", 0)

        # Calculate expected hip position (should be on line from shoulder to ankle)
        expected_hip_y = (shoulder_y + ankle_y) / 2

        # Allow 0.05 tolerance
        tolerance = 0.05

        if hip_y > expected_hip_y + tolerance:
            return "sagging"
        elif hip_y < expected_hip_y - tolerance:
            return "piking"

        return "good"

    def _check_shoulder_position(self, keypoints: Dict) -> bool:
        """Check if shoulders are aligned over elbows."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_elbow = keypoints.get("left_elbow", {})

        if not left_shoulder or not left_elbow:
            return False

        # Shoulders should be roughly aligned horizontally with elbows
        shoulder_x = left_shoulder.get("x", 0)
        elbow_x = left_elbow.get("x", 0)

        # Check horizontal distance
        distance = abs(shoulder_x - elbow_x)

        # If shoulders are too far forward or back, it's misaligned
        return distance > 0.08

    def _check_core_engagement(self, keypoints: Dict) -> bool:
        """Check core engagement by analyzing body line."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})

        if not all([left_shoulder, left_hip, left_knee]):
            return False

        # Calculate angle at hip
        angle = self.estimator.calculate_angle(
            left_shoulder,
            left_hip,
            left_knee
        )

        # In good plank, body should be relatively straight (angle ~170-180)
        # If angle is too small, core is disengaged
        return angle < 160 or angle > 190

    def _check_head_position(self, keypoints: Dict) -> bool:
        """Check if head is in neutral position."""
        nose = keypoints.get("nose", {})
        left_shoulder = keypoints.get("left_shoulder", {})

        if not nose or not left_shoulder:
            return False

        nose_y = nose.get("y", 0)
        shoulder_y = left_shoulder.get("y", 0)

        # Head should be roughly level with shoulders (slightly forward)
        # If head is too far up or down, it's misaligned
        distance = abs(nose_y - shoulder_y)

        return distance > 0.15
