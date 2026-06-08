from typing import Dict, Any
from app.pose_estimator.base import PoseEstimator


class LungeRule:
    """Lunge form analysis with continuous severity-weighted scoring."""

    def __init__(self, estimator: PoseEstimator):
        self.estimator = estimator

    async def analyze(self, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        score = 10.0

        keypoints = pose_data.get("keypoints", {})
        if not keypoints:
            return {"exercise": "lunge", "score": 5.0, "issues": [], "is_good_form": False,
                    "keypoints_analyzed": 0}

        # Only evaluate when person is actually in a lunge (hip lowered)
        in_lunge = self._is_in_lunge_position(keypoints)

        # Knee past toes
        knee_fwd = self._knee_forward_severity(keypoints) if in_lunge else 0.0
        score -= 2.0 * knee_fwd
        if knee_fwd > 0.25:
            issues.append({
                "type": "knee_over_toes",
                "severity": "high" if knee_fwd > 0.6 else "medium",
                "description": "앞 무릎이 발끝을 넘어가고 있습니다",
                "correction": "체중을 뒤로 옮겨 무릎이 발목 위에 오도록 유지하세요"
            })

        # Insufficient depth (only in lunge position)
        depth = self._depth_severity(keypoints) if in_lunge else 0.0
        score -= 2.0 * depth
        if depth > 0.3:
            issues.append({
                "type": "insufficient_depth",
                "severity": "medium" if depth > 0.6 else "low",
                "description": "앞 무릎이 충분히 굽혀지지 않았습니다",
                "correction": "앞 허벅지가 바닥과 평행이 될 때까지 낮추세요"
            })

        # Torso lean
        torso = self._torso_lean_severity(keypoints)
        score -= 3.0 * torso
        if torso > 0.2:
            issues.append({
                "type": "torso_lean",
                "severity": "high" if torso > 0.5 else "medium",
                "description": "상체가 앞으로 너무 기울었습니다",
                "correction": "가슴을 펴고 상체를 곧게 세우세요"
            })

        final = round(max(0.0, min(10.0, score)), 2)
        return {
            "exercise": "lunge",
            "score": final,
            "issues": issues,
            "is_good_form": final >= 7.5,
            "keypoints_analyzed": len(keypoints),
        }

    def _is_in_lunge_position(self, keypoints: Dict) -> bool:
        """Return True when the hip is clearly lowered (in lunge, not standing)."""
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})
        if not left_hip or not left_knee:
            return False
        # Hip should be at or below knee height in a real lunge
        return left_hip.get("y", 0) >= left_knee.get("y", 0) - 0.10

    def _knee_forward_severity(self, keypoints: Dict) -> float:
        left_knee = keypoints.get("left_knee", {})
        left_ankle = keypoints.get("left_ankle", {})
        if not left_knee or not left_ankle:
            return 0.0
        horiz = abs(left_knee.get("x", 0) - left_ankle.get("x", 0))
        # Ideal: knee directly over ankle (horiz ≤ 0.06). Maximum bad: 0.20+
        if horiz <= 0.06:
            return 0.0
        return min(1.0, (horiz - 0.06) / 0.14)

    def _depth_severity(self, keypoints: Dict) -> float:
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})
        left_ankle = keypoints.get("left_ankle", {})
        if not all([left_hip, left_knee, left_ankle]):
            return 0.0
        angle = self.estimator.calculate_angle(left_hip, left_knee, left_ankle)
        # Ideal ≤ 100°; begins penalising above 105°; max penalty at 140°+
        if angle <= 105:
            return 0.0
        return min(1.0, (angle - 105) / 35.0)

    def _torso_lean_severity(self, keypoints: Dict) -> float:
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})
        if not left_shoulder or not left_hip:
            return 0.0
        # For side-view camera, torso lean shows as difference in x between shoulder and hip
        horiz_drift = abs(left_shoulder.get("x", 0) - left_hip.get("x", 0))
        # Ideal: ≤ 0.05. Max bad: 0.20+
        if horiz_drift <= 0.05:
            return 0.0
        return min(1.0, (horiz_drift - 0.05) / 0.15)
