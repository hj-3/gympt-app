"""MediaPipe Pose Estimator implementation."""
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import cv2

from app.pose_estimator.base import PoseEstimator
from app.schemas.pose import PoseLandmark, PoseLandmarks

logger = logging.getLogger(__name__)


class MediaPipePoseEstimator(PoseEstimator):
    """Real pose estimator using MediaPipe Pose solution."""

    # MediaPipe landmark indices mapping
    LANDMARK_NAMES = {
        0: "nose",
        11: "left_shoulder",
        12: "right_shoulder",
        13: "left_elbow",
        14: "right_elbow",
        15: "left_wrist",
        16: "right_wrist",
        23: "left_hip",
        24: "right_hip",
        25: "left_knee",
        26: "right_knee",
        27: "left_ankle",
        28: "right_ankle",
    }

    def __init__(self, enable_gpu: bool = False):
        """
        Initialize MediaPipe Pose estimator.

        Args:
            enable_gpu: Whether to use GPU acceleration
        """
        self.enable_gpu = enable_gpu
        self.frame_count = 0

        try:
            import mediapipe as mp
            self.mp = mp
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils

            # Initialize pose solution
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,  # 0=Lite, 1=Full, 2=Heavy
                smooth_landmarks=True,
                enable_segmentation=False,
                smooth_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )

            logger.info(f"MediaPipe Pose initialized (GPU: {enable_gpu})")

        except ImportError as e:
            logger.error(f"MediaPipe not installed: {e}")
            raise RuntimeError(
                "MediaPipe is required for pose estimation. "
                "Install with: pip install mediapipe"
            )

    async def estimate(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Estimate pose from video frame using MediaPipe.

        Args:
            frame: Video frame as numpy array (height, width, channels)

        Returns:
            Dict containing landmarks, confidence, and keypoints
        """
        self.frame_count += 1

        try:
            # Preprocess frame
            processed_frame = self._preprocess_frame(frame)

            # Convert BGR to RGB (OpenCV uses BGR, MediaPipe uses RGB)
            rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)

            # Process frame with MediaPipe
            results = self.pose.process(rgb_frame)

            if not results.pose_landmarks:
                logger.warning(f"No pose detected in frame {self.frame_count}")
                return self._empty_result()

            # Extract landmarks
            landmarks = self._extract_landmarks(results.pose_landmarks)
            keypoints = self._extract_keypoints(results.pose_landmarks)
            confidence = self._calculate_confidence(results.pose_landmarks)

            return {
                "landmarks": landmarks,
                "confidence": confidence,
                "keypoints": keypoints,
                "frame_number": self.frame_count,
                "pose_world_landmarks": results.pose_world_landmarks,
            }

        except Exception as e:
            logger.error(f"Error processing frame {self.frame_count}: {e}")
            return self._empty_result()

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for optimal pose detection.

        Args:
            frame: Input frame

        Returns:
            Preprocessed frame
        """
        # Resize if too large (performance optimization)
        height, width = frame.shape[:2]

        if height > 480 or width > 640:
            # Maintain aspect ratio
            if height > width:
                new_height = 480
                new_width = int(width * (480 / height))
            else:
                new_width = 640
                new_height = int(height * (640 / width))

            frame = cv2.resize(frame, (new_width, new_height))
            logger.debug(f"Resized frame from {width}x{height} to {new_width}x{new_height}")

        return frame

    def _extract_landmarks(self, pose_landmarks) -> List[Dict[str, float]]:
        """
        Extract all 33 landmarks from MediaPipe results.

        Args:
            pose_landmarks: MediaPipe pose landmarks

        Returns:
            List of 33 landmarks with x, y, z, visibility
        """
        landmarks = []

        for landmark in pose_landmarks.landmark:
            landmarks.append({
                "x": landmark.x,
                "y": landmark.y,
                "z": landmark.z,
                "visibility": landmark.visibility
            })

        return landmarks

    def _extract_keypoints(self, pose_landmarks) -> Dict[str, Dict[str, float]]:
        """
        Extract specific keypoints for exercise analysis.

        Args:
            pose_landmarks: MediaPipe pose landmarks

        Returns:
            Dict of named keypoints with coordinates and confidence
        """
        keypoints = {}

        for idx, name in self.LANDMARK_NAMES.items():
            if idx < len(pose_landmarks.landmark):
                landmark = pose_landmarks.landmark[idx]
                keypoints[name] = {
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z,
                    "confidence": landmark.visibility
                }

        return keypoints

    def _calculate_confidence(self, pose_landmarks) -> float:
        """
        Calculate overall pose detection confidence.

        Args:
            pose_landmarks: MediaPipe pose landmarks

        Returns:
            Average visibility score as confidence
        """
        visibilities = [lm.visibility for lm in pose_landmarks.landmark]
        return sum(visibilities) / len(visibilities) if visibilities else 0.0

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when no pose is detected."""
        return {
            "landmarks": [{"x": 0, "y": 0, "z": 0, "visibility": 0}] * 33,
            "confidence": 0.0,
            "keypoints": {},
            "frame_number": self.frame_count,
        }

    def get_keypoint(self, landmarks: Any, keypoint_name: str) -> Dict[str, float]:
        """
        Get specific keypoint coordinates.

        Args:
            landmarks: Landmarks data (dict or list)
            keypoint_name: Name of the keypoint

        Returns:
            Keypoint coordinates with confidence
        """
        if isinstance(landmarks, dict) and "keypoints" in landmarks:
            return landmarks["keypoints"].get(
                keypoint_name,
                {"x": 0, "y": 0, "z": 0, "confidence": 0}
            )
        return {"x": 0, "y": 0, "z": 0, "confidence": 0}

    def to_pydantic_landmarks(self, landmarks_data: Dict[str, Any]) -> Optional[PoseLandmarks]:
        """
        Convert raw landmarks to Pydantic model.

        Args:
            landmarks_data: Raw landmarks dictionary

        Returns:
            PoseLandmarks model or None if invalid
        """
        try:
            landmarks = [
                PoseLandmark(**lm) for lm in landmarks_data.get("landmarks", [])
            ]

            if len(landmarks) != 33:
                logger.warning(f"Expected 33 landmarks, got {len(landmarks)}")
                return None

            return PoseLandmarks(
                landmarks=landmarks,
                confidence=landmarks_data.get("confidence", 0.0)
            )
        except Exception as e:
            logger.error(f"Error converting landmarks to Pydantic model: {e}")
            return None

    def __del__(self):
        """Clean up MediaPipe resources."""
        if hasattr(self, 'pose'):
            self.pose.close()
            logger.debug("MediaPipe Pose closed")
