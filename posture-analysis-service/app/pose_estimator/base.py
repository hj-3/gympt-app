from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np


class PoseEstimator(ABC):
    """Base class for pose estimation models."""
    
    @abstractmethod
    async def estimate(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Estimate pose from video frame.
        
        Args:
            frame: Video frame as numpy array (height, width, channels)
            
        Returns:
            Dict containing:
                - landmarks: List of pose landmarks
                - confidence: Overall confidence score
                - keypoints: Detected keypoints with coordinates
        """
        pass
    
    @abstractmethod
    def get_keypoint(self, landmarks: List, keypoint_name: str) -> Dict[str, float]:
        """Get specific keypoint coordinates."""
        pass
    
    def calculate_angle(
        self,
        point1: Dict[str, float],
        point2: Dict[str, float],
        point3: Dict[str, float]
    ) -> float:
        """
        Calculate angle between three points.
        
        Args:
            point1, point2, point3: Points with 'x', 'y' coordinates
            
        Returns:
            Angle in degrees
        """
        import math
        
        # Vectors
        v1 = (point1['x'] - point2['x'], point1['y'] - point2['y'])
        v2 = (point3['x'] - point2['x'], point3['y'] - point2['y'])
        
        # Dot product and magnitudes
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        # Calculate angle
        cos_angle = dot / (mag1 * mag2)
        cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp to [-1, 1]
        angle = math.acos(cos_angle)
        
        return math.degrees(angle)
