"""
Pose estimation using MediaPipe
"""
import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Dict, List, Tuple


class PoseEstimator:
    """MediaPipe Pose estimator"""

    def __init__(
        self,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        enable_segmentation: bool = False,
    ):
        """
        Initialize pose estimator

        Args:
            model_complexity: 0=Lite, 1=Full, 2=Heavy (default: 1)
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
            enable_segmentation: Enable segmentation mask
        """
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.pose = self.mp_pose.Pose(
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            enable_segmentation=enable_segmentation,
        )

    def process_frame(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Process a single frame and extract pose landmarks

        Args:
            frame: BGR image (from cv2)

        Returns:
            Dict with landmarks, or None if no pose detected
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        # Process
        results = self.pose.process(image_rgb)

        if not results.pose_landmarks:
            return None

        # Extract landmarks
        landmarks = self._extract_landmarks(results.pose_landmarks, frame.shape)

        return {
            "landmarks": landmarks,
            "world_landmarks": self._extract_world_landmarks(results.pose_world_landmarks),
            "visibility": self._extract_visibility(results.pose_landmarks),
        }

    def _extract_landmarks(self, pose_landmarks, image_shape) -> List[Dict]:
        """Extract normalized landmarks with pixel coordinates"""
        height, width, _ = image_shape
        landmarks = []

        for idx, landmark in enumerate(pose_landmarks.landmark):
            landmarks.append({
                "id": idx,
                "name": self._get_landmark_name(idx),
                "x": landmark.x,  # Normalized [0, 1]
                "y": landmark.y,  # Normalized [0, 1]
                "z": landmark.z,  # Relative depth
                "visibility": landmark.visibility,
                "pixel_x": int(landmark.x * width),
                "pixel_y": int(landmark.y * height),
            })

        return landmarks

    def _extract_world_landmarks(self, world_landmarks) -> Optional[List[Dict]]:
        """Extract 3D world coordinates (in meters)"""
        if not world_landmarks:
            return None

        landmarks_3d = []
        for idx, landmark in enumerate(world_landmarks.landmark):
            landmarks_3d.append({
                "id": idx,
                "name": self._get_landmark_name(idx),
                "x": landmark.x,  # meters
                "y": landmark.y,  # meters
                "z": landmark.z,  # meters
                "visibility": landmark.visibility,
            })

        return landmarks_3d

    def _extract_visibility(self, pose_landmarks) -> Dict[str, float]:
        """Extract visibility scores for key landmarks"""
        key_points = {
            "left_shoulder": 11,
            "right_shoulder": 12,
            "left_hip": 23,
            "right_hip": 24,
            "left_knee": 25,
            "right_knee": 26,
            "left_ankle": 27,
            "right_ankle": 28,
        }

        visibility = {}
        for name, idx in key_points.items():
            visibility[name] = pose_landmarks.landmark[idx].visibility

        return visibility

    def _get_landmark_name(self, idx: int) -> str:
        """Get landmark name from index"""
        landmark_names = [
            "nose", "left_eye_inner", "left_eye", "left_eye_outer",
            "right_eye_inner", "right_eye", "right_eye_outer",
            "left_ear", "right_ear", "mouth_left", "mouth_right",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_pinky", "right_pinky",
            "left_index", "right_index", "left_thumb", "right_thumb",
            "left_hip", "right_hip", "left_knee", "right_knee",
            "left_ankle", "right_ankle", "left_heel", "right_heel",
            "left_foot_index", "right_foot_index"
        ]

        if 0 <= idx < len(landmark_names):
            return landmark_names[idx]
        return f"landmark_{idx}"

    def calculate_angle(
        self,
        point1: Tuple[float, float, float],
        point2: Tuple[float, float, float],
        point3: Tuple[float, float, float],
    ) -> float:
        """
        Calculate angle between three points (in degrees)

        Args:
            point1: First point (x, y, z)
            point2: Vertex point (x, y, z)
            point3: Third point (x, y, z)

        Returns:
            Angle in degrees
        """
        # Convert to numpy arrays
        p1 = np.array(point1)
        p2 = np.array(point2)
        p3 = np.array(point3)

        # Vectors
        v1 = p1 - p2
        v2 = p3 - p2

        # Angle
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Avoid numerical errors
        angle = np.arccos(cos_angle)

        return np.degrees(angle)

    def draw_landmarks(
        self,
        frame: np.ndarray,
        landmarks: List[Dict],
        connections: bool = True,
    ) -> np.ndarray:
        """
        Draw landmarks on frame

        Args:
            frame: BGR image
            landmarks: List of landmark dicts
            connections: Draw connections between landmarks

        Returns:
            Frame with landmarks drawn
        """
        annotated_frame = frame.copy()

        # Draw landmarks
        for landmark in landmarks:
            x, y = landmark["pixel_x"], landmark["pixel_y"]
            visibility = landmark["visibility"]

            # Color based on visibility
            if visibility > 0.8:
                color = (0, 255, 0)  # Green
            elif visibility > 0.5:
                color = (0, 255, 255)  # Yellow
            else:
                color = (0, 0, 255)  # Red

            cv2.circle(annotated_frame, (x, y), 5, color, -1)

        # Draw connections (simplified)
        if connections:
            connections_list = [
                # Torso
                (11, 12), (11, 23), (12, 24), (23, 24),
                # Arms
                (11, 13), (13, 15), (12, 14), (14, 16),
                # Legs
                (23, 25), (25, 27), (24, 26), (26, 28),
            ]

            for conn in connections_list:
                l1 = landmarks[conn[0]]
                l2 = landmarks[conn[1]]
                if l1["visibility"] > 0.5 and l2["visibility"] > 0.5:
                    cv2.line(
                        annotated_frame,
                        (l1["pixel_x"], l1["pixel_y"]),
                        (l2["pixel_x"], l2["pixel_y"]),
                        (255, 255, 255),
                        2,
                    )

        return annotated_frame

    def close(self):
        """Release resources"""
        self.pose.close()
