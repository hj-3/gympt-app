"""Generate realistic pose landmarks for testing."""
import numpy as np
from typing import Dict, List, Tuple


class LandmarkGenerator:
    """Generate realistic MediaPipe pose landmarks."""

    # MediaPipe 33 landmark indices
    LANDMARK_NAMES = [
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

    @staticmethod
    def generate_squat_landmarks(
        depth: float = 0.5,
        knee_valgus: float = 0.0,
        back_angle: float = 0.0
    ) -> Dict[str, Dict[str, float]]:
        """
        Generate squat pose landmarks.

        Args:
            depth: Squat depth 0-1 (0=standing, 1=deep squat)
            knee_valgus: Knee valgus amount -1 to 1 (negative=varus, positive=valgus)
            back_angle: Back angle in degrees (0=vertical, positive=forward lean)

        Returns:
            Dictionary of keypoints
        """
        # Base standing position
        base_hip_y = 0.50
        base_knee_y = 0.75
        base_ankle_y = 0.90

        # Calculate squat depth effect
        hip_y = base_hip_y + (depth * 0.15)  # Hip drops
        knee_y = base_knee_y - (depth * 0.03)  # Knee rises slightly
        shoulder_y = 0.30 + (depth * 0.05)  # Shoulder drops slightly

        # Apply knee valgus/varus
        knee_x_offset = knee_valgus * 0.05

        # Apply back angle
        shoulder_x_offset = np.sin(np.radians(back_angle)) * 0.1

        keypoints = {
            "nose": {"x": 0.50 + shoulder_x_offset, "y": 0.15, "confidence": 0.95},
            "left_shoulder": {"x": 0.40 + shoulder_x_offset, "y": shoulder_y, "confidence": 0.95},
            "right_shoulder": {"x": 0.60 + shoulder_x_offset, "y": shoulder_y, "confidence": 0.95},
            "left_hip": {"x": 0.42, "y": hip_y, "confidence": 0.95},
            "right_hip": {"x": 0.58, "y": hip_y, "confidence": 0.95},
            "left_knee": {"x": 0.40 + knee_x_offset, "y": knee_y, "confidence": 0.95},
            "right_knee": {"x": 0.60 - knee_x_offset, "y": knee_y, "confidence": 0.95},
            "left_ankle": {"x": 0.38, "y": base_ankle_y, "confidence": 0.95},
            "right_ankle": {"x": 0.62, "y": base_ankle_y, "confidence": 0.95},
        }

        return keypoints

    @staticmethod
    def generate_pushup_landmarks(
        height: float = 0.5,
        elbow_flare: float = 0.0,
        hip_sag: float = 0.0
    ) -> Dict[str, Dict[str, float]]:
        """
        Generate pushup pose landmarks.

        Args:
            height: Height 0-1 (0=down, 1=up)
            elbow_flare: Elbow flare -1 to 1 (0=proper, positive=flared)
            hip_sag: Hip sag 0-1 (0=straight, 1=sagging)

        Returns:
            Dictionary of keypoints
        """
        # Base pushup position
        base_shoulder_y = 0.45
        base_elbow_y = 0.47
        base_wrist_y = 0.52
        base_hip_y = 0.48

        # Calculate height effect
        shoulder_y = base_shoulder_y - (height * 0.10)
        elbow_y = base_elbow_y - (height * 0.08)
        hip_y = base_hip_y - (height * 0.10)

        # Apply hip sag
        hip_y += hip_sag * 0.08

        # Apply elbow flare
        elbow_x_offset = elbow_flare * 0.10

        keypoints = {
            "nose": {"x": 0.50, "y": shoulder_y - 0.10, "confidence": 0.92},
            "left_shoulder": {"x": 0.35, "y": shoulder_y, "confidence": 0.92},
            "right_shoulder": {"x": 0.65, "y": shoulder_y, "confidence": 0.92},
            "left_elbow": {"x": 0.30 - elbow_x_offset, "y": elbow_y, "confidence": 0.90},
            "right_elbow": {"x": 0.70 + elbow_x_offset, "y": elbow_y, "confidence": 0.90},
            "left_wrist": {"x": 0.28, "y": base_wrist_y, "confidence": 0.90},
            "right_wrist": {"x": 0.72, "y": base_wrist_y, "confidence": 0.90},
            "left_hip": {"x": 0.40, "y": hip_y, "confidence": 0.90},
            "right_hip": {"x": 0.60, "y": hip_y, "confidence": 0.90},
            "left_knee": {"x": 0.42, "y": hip_y + 0.15, "confidence": 0.88},
            "right_knee": {"x": 0.58, "y": hip_y + 0.15, "confidence": 0.88},
        }

        return keypoints

    @staticmethod
    def generate_plank_landmarks(
        hip_alignment: float = 0.0,
        time_elapsed: float = 0.0
    ) -> Dict[str, Dict[str, float]]:
        """
        Generate plank pose landmarks.

        Args:
            hip_alignment: Hip alignment -1 to 1 (negative=down, positive=up)
            time_elapsed: Time in seconds (affects form degradation)

        Returns:
            Dictionary of keypoints
        """
        # Form degradation over time
        degradation = min(time_elapsed / 60.0, 1.0) * 0.05

        base_shoulder_y = 0.40
        base_hip_y = 0.42
        base_knee_y = 0.55

        # Apply hip alignment
        hip_y = base_hip_y + (hip_alignment * 0.08) + degradation

        keypoints = {
            "nose": {"x": 0.50, "y": 0.30, "confidence": 0.93},
            "left_shoulder": {"x": 0.35, "y": base_shoulder_y, "confidence": 0.94},
            "right_shoulder": {"x": 0.65, "y": base_shoulder_y, "confidence": 0.94},
            "left_elbow": {"x": 0.33, "y": 0.46, "confidence": 0.92},
            "right_elbow": {"x": 0.67, "y": 0.46, "confidence": 0.92},
            "left_wrist": {"x": 0.32, "y": 0.50, "confidence": 0.92},
            "right_wrist": {"x": 0.68, "y": 0.50, "confidence": 0.92},
            "left_hip": {"x": 0.40, "y": hip_y, "confidence": 0.93},
            "right_hip": {"x": 0.60, "y": hip_y, "confidence": 0.93},
            "left_knee": {"x": 0.42, "y": base_knee_y, "confidence": 0.90},
            "right_knee": {"x": 0.58, "y": base_knee_y, "confidence": 0.90},
        }

        return keypoints

    @staticmethod
    def generate_deadlift_landmarks(
        height: float = 0.5,
        back_rounding: float = 0.0
    ) -> Dict[str, Dict[str, float]]:
        """
        Generate deadlift pose landmarks.

        Args:
            height: Lift height 0-1 (0=bottom, 1=top)
            back_rounding: Back rounding 0-1 (0=neutral, 1=rounded)

        Returns:
            Dictionary of keypoints
        """
        base_hip_y = 0.65
        base_shoulder_y = 0.50
        base_knee_y = 0.75

        # Calculate lift height effect
        hip_y = base_hip_y - (height * 0.15)
        shoulder_y = base_shoulder_y - (height * 0.15)
        knee_y = base_knee_y - (height * 0.05)

        # Apply back rounding
        shoulder_x_offset = back_rounding * 0.10

        keypoints = {
            "nose": {"x": 0.50 + shoulder_x_offset, "y": 0.35, "confidence": 0.92},
            "left_shoulder": {"x": 0.40 + shoulder_x_offset, "y": shoulder_y, "confidence": 0.93},
            "right_shoulder": {"x": 0.60 + shoulder_x_offset, "y": shoulder_y, "confidence": 0.93},
            "left_hip": {"x": 0.42, "y": hip_y, "confidence": 0.93},
            "right_hip": {"x": 0.58, "y": hip_y, "confidence": 0.93},
            "left_knee": {"x": 0.40, "y": knee_y, "confidence": 0.92},
            "right_knee": {"x": 0.60, "y": knee_y, "confidence": 0.92},
            "left_ankle": {"x": 0.38, "y": 0.90, "confidence": 0.92},
            "right_ankle": {"x": 0.62, "y": 0.90, "confidence": 0.92},
        }

        return keypoints

    @staticmethod
    def add_noise(
        keypoints: Dict[str, Dict[str, float]],
        noise_level: float = 0.01
    ) -> Dict[str, Dict[str, float]]:
        """
        Add realistic noise to landmarks.

        Args:
            keypoints: Original keypoints
            noise_level: Noise standard deviation

        Returns:
            Keypoints with noise added
        """
        noisy_keypoints = {}
        for name, point in keypoints.items():
            noisy_keypoints[name] = {
                "x": point["x"] + np.random.normal(0, noise_level),
                "y": point["y"] + np.random.normal(0, noise_level),
                "confidence": max(0.5, min(1.0, point["confidence"] + np.random.normal(0, 0.05)))
            }
        return noisy_keypoints

    @staticmethod
    def generate_rep_sequence(
        exercise: str,
        num_reps: int,
        frames_per_rep: int = 30
    ) -> List[Dict[str, Dict[str, float]]]:
        """
        Generate a sequence of landmarks for multiple reps.

        Args:
            exercise: Exercise type (squat, pushup, etc.)
            num_reps: Number of reps to generate
            frames_per_rep: Number of frames per rep

        Returns:
            List of keypoint dictionaries
        """
        sequence = []

        for rep in range(num_reps):
            # Generate frames for one rep
            for i in range(frames_per_rep):
                # Calculate position in rep (0 to 1)
                position = i / frames_per_rep

                if exercise == "squat":
                    # Squat: down -> up
                    depth = np.sin(position * np.pi)  # 0 -> 1 -> 0
                    keypoints = LandmarkGenerator.generate_squat_landmarks(depth=depth)

                elif exercise == "pushup":
                    # Pushup: down -> up
                    height = 1.0 - np.sin(position * np.pi)  # 1 -> 0 -> 1
                    keypoints = LandmarkGenerator.generate_pushup_landmarks(height=height)

                elif exercise == "deadlift":
                    # Deadlift: up -> down
                    height = np.sin(position * np.pi)
                    keypoints = LandmarkGenerator.generate_deadlift_landmarks(height=height)

                else:
                    raise ValueError(f"Unknown exercise: {exercise}")

                # Add realistic noise
                keypoints = LandmarkGenerator.add_noise(keypoints, noise_level=0.005)

                sequence.append({
                    "landmarks": [],
                    "confidence": 0.85 + np.random.uniform(-0.05, 0.10),
                    "keypoints": keypoints
                })

        return sequence
