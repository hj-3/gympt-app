from typing import Dict, Any
from app.pose_estimator.base import PoseEstimator


class SquatRule:
    """Squat form analysis rules."""
    
    def __init__(self, estimator: PoseEstimator):
        self.estimator = estimator
    
    async def analyze(self, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze squat form.
        
        Checks:
        - Knee valgus (knees caving in)
        - Depth (parallel or below)
        - Back angle (upright torso)
        - Hip hinge
        """
        issues = []
        score = 10.0
        
        keypoints = pose_data.get("keypoints", {})
        
        # Check knee valgus
        knee_valgus = self._check_knee_valgus(keypoints)
        if knee_valgus:
            issues.append({
                "type": "knee_valgus",
                "severity": "medium",
                "description": "무릎이 안쪽으로 모이고 있습니다",
                "correction": "무릎을 바깥으로 밀어 발끝 방향과 정렬하세요"
            })
            score -= 2.0
        
        # Check depth
        depth_issue = self._check_depth(keypoints)
        if depth_issue:
            issues.append({
                "type": "insufficient_depth",
                "severity": "low",
                "description": "충분한 깊이까지 내려가지 않았습니다",
                "correction": "허벅지가 바닥과 평행이 될 때까지 엉덩이를 낮추세요"
            })
            score -= 1.5
        
        # Check back angle
        back_rounding = self._check_back_rounding(keypoints)
        if back_rounding:
            issues.append({
                "type": "back_rounding",
                "severity": "high",
                "description": "허리가 굽고 있습니다",
                "correction": "가슴을 펴고 척추를 중립으로 유지하세요"
            })
            score -= 3.0
        
        return {
            "exercise": "squat",
            "score": max(0.0, score),
            "issues": issues,
            "is_good_form": score >= 8.0,
            "keypoints_analyzed": len(keypoints)
        }
    
    def _check_knee_valgus(self, keypoints: Dict) -> bool:
        """Check if knees are caving inward."""
        left_knee = keypoints.get("left_knee", {})
        right_knee = keypoints.get("right_knee", {})
        left_ankle = keypoints.get("left_ankle", {})
        right_ankle = keypoints.get("right_ankle", {})
        
        if not all([left_knee, right_knee, left_ankle, right_ankle]):
            return False
        
        # Calculate knee-ankle horizontal distance
        left_distance = abs(left_knee.get("x", 0) - left_ankle.get("x", 0))
        right_distance = abs(right_knee.get("x", 0) - right_ankle.get("x", 0))
        
        # If knees are significantly inside ankles, it's valgus
        threshold = 0.05
        return left_distance < threshold or right_distance < threshold
    
    def _check_depth(self, keypoints: Dict) -> bool:
        """Check if squat depth is sufficient."""
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})
        
        if not left_hip or not left_knee:
            return False
        
        # Check if hip is below knee (sufficient depth)
        hip_y = left_hip.get("y", 0)
        knee_y = left_knee.get("y", 0)
        
        # If hip Y is less than knee Y (higher in image), depth is insufficient
        return hip_y < knee_y + 0.05
    
    def _check_back_rounding(self, keypoints: Dict) -> bool:
        """Check if back is rounding."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})
        left_knee = keypoints.get("left_knee", {})
        
        if not all([left_shoulder, left_hip, left_knee]):
            return False
        
        # Calculate torso angle
        angle = self.estimator.calculate_angle(
            left_shoulder,
            left_hip,
            left_knee
        )
        
        # If torso angle is too acute, back is rounding
        return angle < 70 or angle > 110
