from typing import Dict, Any, List
import numpy as np
import random

from app.pose_estimator.base import PoseEstimator


class MockPoseEstimator(PoseEstimator):
    """Mock pose estimator for testing without ML models."""
    
    def __init__(self):
        self.frame_count = 0
    
    async def estimate(self, frame: np.ndarray) -> Dict[str, Any]:
        """Generate mock pose estimation."""
        self.frame_count += 1
        
        # Simulate realistic pose with some variation
        base_confidence = 0.85 + random.uniform(-0.1, 0.1)
        
        # Generate mock landmarks for common body points
        landmarks = self._generate_mock_landmarks()
        
        return {
            "landmarks": landmarks,
            "confidence": base_confidence,
            "keypoints": {
                "nose": {"x": 0.5, "y": 0.2, "confidence": 0.9},
                "left_shoulder": {"x": 0.4, "y": 0.35, "confidence": 0.88},
                "right_shoulder": {"x": 0.6, "y": 0.35, "confidence": 0.87},
                "left_elbow": {"x": 0.35, "y": 0.5, "confidence": 0.85},
                "right_elbow": {"x": 0.65, "y": 0.5, "confidence": 0.86},
                "left_wrist": {"x": 0.3, "y": 0.65, "confidence": 0.82},
                "right_wrist": {"x": 0.7, "y": 0.65, "confidence": 0.83},
                "left_hip": {"x": 0.42, "y": 0.6, "confidence": 0.89},
                "right_hip": {"x": 0.58, "y": 0.6, "confidence": 0.88},
                "left_knee": {"x": 0.4, "y": 0.75, "confidence": 0.87},
                "right_knee": {"x": 0.6, "y": 0.75, "confidence": 0.86},
                "left_ankle": {"x": 0.38, "y": 0.9, "confidence": 0.85},
                "right_ankle": {"x": 0.62, "y": 0.9, "confidence": 0.84},
            },
            "frame_number": self.frame_count
        }
    
    def get_keypoint(self, landmarks: List, keypoint_name: str) -> Dict[str, float]:
        """Get specific keypoint from landmarks."""
        # For mock, just return from keypoints dict
        if isinstance(landmarks, dict) and "keypoints" in landmarks:
            return landmarks["keypoints"].get(keypoint_name, {"x": 0, "y": 0, "confidence": 0})
        return {"x": 0, "y": 0, "confidence": 0}
    
    def _generate_mock_landmarks(self) -> List[Dict[str, float]]:
        """Generate list of mock landmarks."""
        # Simulate MediaPipe-style 33 landmarks
        landmarks = []
        for i in range(33):
            landmarks.append({
                "x": random.uniform(0.2, 0.8),
                "y": random.uniform(0.1, 0.9),
                "z": random.uniform(-0.5, 0.5),
                "visibility": random.uniform(0.7, 0.95)
            })
        return landmarks
