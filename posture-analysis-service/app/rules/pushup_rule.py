from typing import Dict, Any
from app.pose_estimator.base import PoseEstimator


class PushupRule:
    """Push-up form analysis with continuous severity-weighted scoring."""

    def __init__(self, estimator: PoseEstimator):
        self.estimator = estimator

    async def analyze(self, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        issues = []
        score = 10.0

        keypoints = pose_data.get("keypoints", {})
        if not keypoints:
            return {"exercise": "pushup", "score": 5.0, "issues": [], "is_good_form": False,
                    "keypoints_analyzed": 0}

        # Elbow flare — only meaningful at the bottom of the movement
        flare = self._elbow_flare_severity(keypoints)
        score -= 2.5 * flare
        if flare > 0.25:
            issues.append({
                "type": "elbow_flare",
                "severity": "high" if flare > 0.6 else "medium",
                "description": "팔꿈치가 너무 벌어져 있습니다",
                "correction": "팔꿈치를 몸쪽으로 붙여 약 45도를 유지하세요"
            })

        # Hip sag — body not in straight line
        sag = self._hip_sag_severity(keypoints)
        score -= 3.5 * sag
        if sag > 0.2:
            issues.append({
                "type": "hip_sag",
                "severity": "high" if sag > 0.5 else "medium",
                "description": "엉덩이가 처지고 있습니다",
                "correction": "코어에 힘을 주고 머리부터 발뒤꿈치까지 일직선을 유지하세요"
            })

        # Range of motion — only penalise when in the DOWN phase
        rom = self._rom_severity(keypoints)
        score -= 2.0 * rom
        if rom > 0.3:
            issues.append({
                "type": "insufficient_rom",
                "severity": "medium" if rom > 0.6 else "low",
                "description": "가슴을 충분히 낮추지 않았습니다",
                "correction": "가슴이 바닥에 거의 닿을 때까지 내려가세요"
            })

        final = round(max(0.0, min(10.0, score)), 2)
        return {
            "exercise": "pushup",
            "score": final,
            "issues": issues,
            "is_good_form": final >= 7.5,
            "keypoints_analyzed": len(keypoints),
        }

    def _elbow_flare_severity(self, keypoints: Dict) -> float:
        left_shoulder = keypoints.get("left_shoulder", {})
        left_elbow = keypoints.get("left_elbow", {})
        left_wrist = keypoints.get("left_wrist", {})
        if not all([left_shoulder, left_elbow, left_wrist]):
            return 0.0

        # Only flag when in down position: elbow clearly below shoulder (y increases down)
        elbow_y = left_elbow.get("y", 0)
        shoulder_y = left_shoulder.get("y", 0)
        if elbow_y < shoulder_y + 0.04:
            return 0.0  # Not in down position

        # Horizontal flare: ideal ≤ 0.08, maximum bad ≥ 0.22
        horiz = abs(left_elbow.get("x", 0) - left_shoulder.get("x", 0))
        if horiz <= 0.08:
            return 0.0
        return min(1.0, (horiz - 0.08) / 0.14)

    def _hip_sag_severity(self, keypoints: Dict) -> float:
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})
        left_ankle = keypoints.get("left_ankle", {})
        if not all([left_shoulder, left_hip, left_ankle]):
            return 0.0

        shoulder_y = left_shoulder.get("y", 0)
        hip_y = left_hip.get("y", 0)
        ankle_y = left_ankle.get("y", 0)

        # Expected hip on the line from shoulder to ankle
        expected = shoulder_y + (ankle_y - shoulder_y) * 0.5
        sag_amount = hip_y - expected  # positive = sagging down
        if sag_amount <= 0.03:
            return 0.0
        return min(1.0, (sag_amount - 0.03) / 0.12)

    def _rom_severity(self, keypoints: Dict) -> float:
        left_shoulder = keypoints.get("left_shoulder", {})
        left_elbow = keypoints.get("left_elbow", {})
        if not left_shoulder or not left_elbow:
            return 0.0

        elbow_y = left_elbow.get("y", 0)
        shoulder_y = left_shoulder.get("y", 0)

        # Only in down phase: elbow should be below shoulder
        if elbow_y <= shoulder_y:
            return 0.0  # Not in down position — don't penalise

        # When down, elbow-shoulder vertical distance should be ≥ 0.12 (deep enough)
        depth = elbow_y - shoulder_y
        if depth >= 0.12:
            return 0.0
        return min(1.0, (0.12 - depth) / 0.10)
