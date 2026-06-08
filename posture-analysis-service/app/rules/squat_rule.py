from typing import Dict, Any
from app.pose_estimator.base import PoseEstimator


class SquatRule:
    """Squat form analysis with continuous severity-weighted scoring."""

    def __init__(self, estimator: PoseEstimator):
        self.estimator = estimator

    async def analyze(self, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        score = 10.0

        keypoints = pose_data.get("keypoints", {})
        if not keypoints:
            return {"exercise": "squat", "score": 5.0, "issues": [], "is_good_form": False,
                    "keypoints_analyzed": 0}

        # Knee valgus — severity 0..1 → max -2.5 pts
        valgus = self._knee_valgus_severity(keypoints)
        score -= 2.5 * valgus
        if valgus > 0.2:
            issues.append({
                "type": "knee_valgus",
                "severity": "high" if valgus > 0.6 else "medium",
                "description": "무릎이 안쪽으로 모이고 있습니다",
                "correction": "무릎을 바깥으로 밀어 발끝 방향과 정렬하세요"
            })

        # Insufficient depth — only when in squat position
        depth = self._depth_severity(keypoints)
        score -= 2.0 * depth
        if depth > 0.25:
            issues.append({
                "type": "insufficient_depth",
                "severity": "medium" if depth > 0.5 else "low",
                "description": "충분한 깊이까지 내려가지 않았습니다",
                "correction": "허벅지가 바닥과 평행이 될 때까지 엉덩이를 낮추세요"
            })

        # Back rounding — shoulder-hip-knee angle deviation
        back = self._back_rounding_severity(keypoints)
        score -= 3.0 * back
        if back > 0.2:
            issues.append({
                "type": "back_rounding",
                "severity": "high" if back > 0.5 else "medium",
                "description": "허리가 굽고 있습니다",
                "correction": "가슴을 펴고 척추를 중립으로 유지하세요"
            })

        final = round(max(0.0, min(10.0, score)), 2)
        return {
            "exercise": "squat",
            "score": final,
            "issues": issues,
            "is_good_form": final >= 7.5,
            "keypoints_analyzed": len(keypoints),
        }

    # ── Severity helpers (return 0.0 = perfect, 1.0 = maximum bad) ──────────

    def _knee_valgus_severity(self, keypoints: Dict) -> float:
        left_knee = keypoints.get("left_knee", {})
        right_knee = keypoints.get("right_knee", {})
        left_ankle = keypoints.get("left_ankle", {})
        right_ankle = keypoints.get("right_ankle", {})
        if not all([left_knee, right_knee, left_ankle, right_ankle]):
            return 0.0

        l_dist = abs(left_knee.get("x", 0) - left_ankle.get("x", 0))
        r_dist = abs(right_knee.get("x", 0) - right_ankle.get("x", 0))
        # ideal: knee ≥ 0.06 outside ankle; valgus starts below 0.06
        ideal = 0.06
        worst = min(l_dist, r_dist)
        if worst >= ideal:
            return 0.0
        return min(1.0, (ideal - worst) / ideal)

    def _depth_severity(self, keypoints: Dict) -> float:
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})
        if not left_hip or not left_knee:
            return 0.0

        hip_y = left_hip.get("y", 0)
        knee_y = left_knee.get("y", 0)

        # Only flag when person is in the squat position (hip near knee level)
        in_squat = hip_y >= knee_y - 0.12
        if not in_squat:
            return 0.0

        # Ideal: hip_y ≥ knee_y (parallel or below). Penalty increases as hip stays high.
        if hip_y >= knee_y:
            return 0.0
        shortfall = knee_y - hip_y  # 0.0 = parallel, larger = less deep
        return min(1.0, shortfall / 0.15)

    def _back_rounding_severity(self, keypoints: Dict) -> float:
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})
        if not all([left_shoulder, left_hip, left_knee]):
            return 0.0

        angle = self.estimator.calculate_angle(left_shoulder, left_hip, left_knee)
        # Standing straight ≈ 170-180°. Rounding starts below 150°.
        ideal_min = 150.0
        if angle >= ideal_min:
            return 0.0
        return min(1.0, (ideal_min - angle) / 70.0)
