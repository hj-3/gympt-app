from typing import Dict, Any
from app.pose_estimator.base import PoseEstimator


class PushupRule:
    """Push-up form analysis rules."""
    
    def __init__(self, estimator: PoseEstimator):
        self.estimator = estimator
    
    async def analyze(self, pose_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze push-up form.
        
        Checks:
        - Elbow flare (elbows too wide)
        - Hip sag (core engagement)
        - Range of motion
        - Shoulder alignment
        """
        issues = []
        score = 10.0
        
        keypoints = pose_data.get("keypoints", {})
        
        # Check elbow flare
        elbow_flare = self._check_elbow_flare(keypoints)
        if elbow_flare:
            issues.append({
                "type": "elbow_flare",
                "severity": "medium",
                "description": "팔꿈치가 너무 벌어져 있습니다",
                "correction": "팔꿈치를 몸쪽으로 붙여 약 45도를 유지하세요"
            })
            score -= 2.0
        
        # Check hip sag
        hip_sag = self._check_hip_sag(keypoints)
        if hip_sag:
            issues.append({
                "type": "hip_sag",
                "severity": "high",
                "description": "엉덩이가 처지고 있습니다",
                "correction": "코어에 힘을 주고 머리부터 발뒤꿈치까지 일직선을 유지하세요"
            })
            score -= 3.0
        
        # Check range of motion
        rom_issue = self._check_range_of_motion(keypoints)
        if rom_issue:
            issues.append({
                "type": "insufficient_rom",
                "severity": "low",
                "description": "가슴을 충분히 낮추지 않았습니다",
                "correction": "가슴이 바닥에 거의 닿을 때까지 내려가세요"
            })
            score -= 1.5
        
        return {
            "exercise": "pushup",
            "score": max(0.0, score),
            "issues": issues,
            "is_good_form": score >= 8.0,
            "keypoints_analyzed": len(keypoints)
        }
    
    def _check_elbow_flare(self, keypoints: Dict) -> bool:
        """Check if elbows are flaring too wide."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_elbow = keypoints.get("left_elbow", {})
        left_wrist = keypoints.get("left_wrist", {})
        
        if not all([left_shoulder, left_elbow, left_wrist]):
            return False
        
        # Calculate elbow angle
        angle = self.estimator.calculate_angle(
            left_shoulder,
            left_elbow,
            left_wrist
        )
        
        # If angle is too wide, elbows are flaring
        return angle > 75
    
    def _check_hip_sag(self, keypoints: Dict) -> bool:
        """Check if hips are sagging."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_hip = keypoints.get("left_hip", {})
        left_ankle = keypoints.get("left_ankle", {})
        
        if not all([left_shoulder, left_hip, left_ankle]):
            return False
        
        # Check if hip Y is significantly below the line from shoulder to ankle
        shoulder_y = left_shoulder.get("y", 0)
        hip_y = left_hip.get("y", 0)
        ankle_y = left_ankle.get("y", 0)
        
        # Expected hip Y (midpoint)
        expected_hip_y = (shoulder_y + ankle_y) / 2
        
        # If hip is too low, it's sagging
        return hip_y > expected_hip_y + 0.1
    
    def _check_range_of_motion(self, keypoints: Dict) -> bool:
        """Check if ROM is sufficient."""
        left_shoulder = keypoints.get("left_shoulder", {})
        left_elbow = keypoints.get("left_elbow", {})
        
        if not left_shoulder or not left_elbow:
            return False
        
        # Check vertical distance between shoulder and elbow
        distance = abs(left_shoulder.get("y", 0) - left_elbow.get("y", 0))
        
        # If distance is too small, not lowering enough
        return distance < 0.15
