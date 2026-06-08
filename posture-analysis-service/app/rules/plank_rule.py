"""Plank form analysis with continuous severity-weighted scoring."""
from typing import Dict, Any
from app.pose_estimator.base import PoseEstimator


class PlankRule:
    """Plank form analysis rules."""

    def __init__(self, estimator: PoseEstimator):
        self.estimator = estimator

    async def analyze(self, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        score = 10.0

        keypoints = pose_data.get("keypoints", {})
        if not keypoints:
            return {"exercise": "plank", "score": 5.0, "issues": [], "is_good_form": False,
                    "keypoints_analyzed": 0}

        # Hip alignment: sagging or piking
        hip_sag, hip_pike = self._hip_deviation_severity(keypoints)
        score -= 3.5 * hip_sag
        if hip_sag > 0.2:
            issues.append({
                "type": "hip_sag",
                "severity": "high" if hip_sag > 0.5 else "medium",
                "description": "엉덩이가 아래로 처지고 있습니다",
                "correction": "코어에 힘을 주고 엉덩이를 어깨 높이에 맞춰 올리세요"
            })
        score -= 2.5 * hip_pike
        if hip_pike > 0.2:
            issues.append({
                "type": "hip_pike",
                "severity": "medium",
                "description": "엉덩이가 너무 높습니다",
                "correction": "엉덩이를 낮춰 머리부터 발뒤꿈치까지 일직선을 만드세요"
            })

        # Core engagement: shoulder–hip–knee angle (good plank ≈ 165–180°)
        core = self._core_severity(keypoints)
        score -= 3.0 * core
        if core > 0.25:
            issues.append({
                "type": "poor_core_engagement",
                "severity": "high" if core > 0.6 else "medium",
                "description": "코어에 힘이 빠져 있습니다",
                "correction": "복근에 힘을 주고 척추를 중립으로 유지하세요"
            })

        # Head/neck alignment
        head = self._head_severity(keypoints)
        score -= 1.5 * head
        if head > 0.3:
            issues.append({
                "type": "head_misalignment",
                "severity": "low",
                "description": "머리가 중립 위치에 있지 않습니다",
                "correction": "목을 중립으로 유지하고 시선은 바닥을 향하세요"
            })

        final = round(max(0.0, min(10.0, score)), 2)
        return {
            "exercise": "plank",
            "score": final,
            "issues": issues,
            "is_good_form": final >= 7.5,
            "keypoints_analyzed": len(keypoints),
        }

    def _hip_deviation_severity(self, keypoints: Dict):
        """Return (sag_severity, pike_severity), each 0..1."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})
        left_ankle = keypoints.get("left_ankle", {})
        if not all([left_shoulder, left_hip, left_ankle]):
            return 0.0, 0.0

        shoulder_y = left_shoulder.get("y", 0)
        ankle_y = left_ankle.get("y", 0)
        hip_y = left_hip.get("y", 0)

        # Linear interpolation: where should hip be along shoulder-to-ankle line?
        # shoulder_y and ankle_y: which is higher (smaller y) in side-view plank?
        # typically shoulder is higher than ankle (shoulder_y < ankle_y if feet on floor)
        expected_y = shoulder_y + (ankle_y - shoulder_y) * 0.45  # hip ~45% along line
        deviation = hip_y - expected_y  # positive = too low (sagging), negative = too high (piking)

        tolerance = 0.04
        if abs(deviation) <= tolerance:
            return 0.0, 0.0

        if deviation > tolerance:  # sagging
            sag = min(1.0, (deviation - tolerance) / 0.12)
            return sag, 0.0
        else:  # piking
            pike = min(1.0, (-deviation - tolerance) / 0.10)
            return 0.0, pike

    def _core_severity(self, keypoints: Dict) -> float:
        """Body straightness: shoulder-hip-knee angle should be ~165-180°."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})
        if not all([left_shoulder, left_hip, left_knee]):
            return 0.0

        angle = self.estimator.calculate_angle(left_shoulder, left_hip, left_knee)
        # calculate_angle returns 0-180 via arccos. Good plank ≥ 160°.
        if angle >= 160:
            return 0.0
        return min(1.0, (160 - angle) / 50.0)

    def _head_severity(self, keypoints: Dict) -> float:
        nose = keypoints.get("nose", {})
        left_shoulder = keypoints.get("left_shoulder", {})
        if not nose or not left_shoulder:
            return 0.0
        distance = abs(nose.get("y", 0) - left_shoulder.get("y", 0))
        # Ideal ≤ 0.12; max bad: 0.25+
        if distance <= 0.12:
            return 0.0
        return min(1.0, (distance - 0.12) / 0.13)
