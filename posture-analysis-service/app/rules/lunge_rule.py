from typing import Dict, Any
from app.pose_estimator.base import PoseEstimator


class LungeRule:
    """Lunge form analysis rules."""

    def __init__(self, estimator: PoseEstimator):
        self.estimator = estimator

    async def analyze(self, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze lunge form.

        Checks:
        - Front knee over toes (knee tracking past the ankle)
        - Front knee depth (should reach ~90 degrees)
        - Torso uprightness
        """
        issues = []
        score = 10.0

        keypoints = pose_data.get("keypoints", {})

        # Check front knee passing over toes
        knee_over_toes = self._check_knee_over_toes(keypoints)
        if knee_over_toes:
            issues.append({
                "type": "knee_over_toes",
                "severity": "medium",
                "description": "앞 무릎이 발끝을 넘어가고 있습니다",
                "correction": "체중을 뒤로 옮겨 무릎이 발목 위에 오도록 유지하세요"
            })
            score -= 2.0

        # Check front knee depth
        shallow_depth = self._check_depth(keypoints)
        if shallow_depth:
            issues.append({
                "type": "insufficient_depth",
                "severity": "low",
                "description": "앞 무릎이 충분히 굽혀지지 않았습니다",
                "correction": "앞 허벅지가 바닥과 평행이 될 때까지 낮추세요"
            })
            score -= 1.5

        # Check torso uprightness
        torso_lean = self._check_torso_lean(keypoints)
        if torso_lean:
            issues.append({
                "type": "torso_lean",
                "severity": "high",
                "description": "상체가 앞으로 너무 기울었습니다",
                "correction": "가슴을 펴고 상체를 곧게 세우세요"
            })
            score -= 3.0

        return {
            "exercise": "lunge",
            "score": max(0.0, score),
            "issues": issues,
            "is_good_form": score >= 8.0,
            "keypoints_analyzed": len(keypoints)
        }

    def _check_knee_over_toes(self, keypoints: Dict) -> bool:
        """Check if the front knee travels horizontally past the ankle."""
        left_knee = keypoints.get("left_knee", {})
        left_ankle = keypoints.get("left_ankle", {})

        if not left_knee or not left_ankle:
            return False

        # Horizontal distance between knee and ankle
        horizontal_offset = abs(left_knee.get("x", 0) - left_ankle.get("x", 0))

        # Large horizontal offset means the knee is past the toes
        return horizontal_offset > 0.12

    def _check_depth(self, keypoints: Dict) -> bool:
        """Check whether the front knee bends to roughly 90 degrees."""
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})
        left_ankle = keypoints.get("left_ankle", {})

        if not all([left_hip, left_knee, left_ankle]):
            return False

        knee_angle = self.estimator.calculate_angle(left_hip, left_knee, left_ankle)

        # A proper lunge reaches ~90 degrees; much larger means too shallow
        return knee_angle > 120

    def _check_torso_lean(self, keypoints: Dict) -> bool:
        """Check if the torso is leaning forward instead of staying upright."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})

        if not left_shoulder or not left_hip:
            return False

        # Horizontal drift between shoulder and hip indicates forward lean
        horizontal_drift = abs(left_shoulder.get("x", 0) - left_hip.get("x", 0))

        return horizontal_drift > 0.12
