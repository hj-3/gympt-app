"""
Exercise form analysis service
"""
from typing import Dict, List, Optional, Tuple
import numpy as np

from ..config.settings import settings


class FormAnalyzer:
    """Analyze exercise form and provide feedback"""

    def __init__(self):
        self.exercise_validators = {
            "squat": self._analyze_squat,
            "pushup": self._analyze_pushup,
            "push-up": self._analyze_pushup,
            "deadlift": self._analyze_deadlift,
            "plank": self._analyze_plank,
        }

    def analyze(
        self,
        exercise: str,
        landmarks: List[Dict],
        rep_phase: Optional[str] = None,
    ) -> Dict:
        """
        Analyze form for a specific exercise

        Args:
            exercise: Exercise name (squat, pushup, deadlift, etc.)
            landmarks: List of pose landmarks
            rep_phase: Optional rep phase (down, up, hold)

        Returns:
            Analysis results with score and feedback
        """
        exercise_lower = exercise.lower()

        if exercise_lower not in self.exercise_validators:
            return {
                "exercise": exercise,
                "form_score": 0,
                "is_valid": False,
                "error": f"Unknown exercise: {exercise}",
                "feedback": [],
            }

        # Call exercise-specific validator
        validator = self.exercise_validators[exercise_lower]
        result = validator(landmarks, rep_phase)

        return result

    def _analyze_squat(self, landmarks: List[Dict], rep_phase: Optional[str]) -> Dict:
        """Analyze squat form"""
        feedback = []
        deductions = []

        # Get key landmarks
        left_hip = self._get_landmark(landmarks, "left_hip")
        right_hip = self._get_landmark(landmarks, "right_hip")
        left_knee = self._get_landmark(landmarks, "left_knee")
        right_knee = self._get_landmark(landmarks, "right_knee")
        left_ankle = self._get_landmark(landmarks, "left_ankle")
        right_ankle = self._get_landmark(landmarks, "right_ankle")
        left_shoulder = self._get_landmark(landmarks, "left_shoulder")
        right_shoulder = self._get_landmark(landmarks, "right_shoulder")

        if not all([left_hip, right_hip, left_knee, right_knee, left_ankle, right_ankle]):
            return {
                "exercise": "squat",
                "form_score": 0,
                "is_valid": False,
                "error": "Could not detect all required landmarks",
                "feedback": ["Make sure your full body is visible in the camera"],
            }

        # Calculate angles
        left_hip_angle = self._calculate_angle_from_landmarks(
            left_shoulder, left_hip, left_knee
        )
        right_hip_angle = self._calculate_angle_from_landmarks(
            right_shoulder, right_hip, right_knee
        )
        hip_angle = (left_hip_angle + right_hip_angle) / 2

        left_knee_angle = self._calculate_angle_from_landmarks(
            left_hip, left_knee, left_ankle
        )
        right_knee_angle = self._calculate_angle_from_landmarks(
            right_hip, right_knee, right_ankle
        )
        knee_angle = (left_knee_angle + right_knee_angle) / 2

        # Check depth (hip angle)
        if rep_phase == "down" or rep_phase is None:
            if hip_angle < settings.SQUAT_HIP_ANGLE_MIN:
                feedback.append("Going too low - risk of knee injury")
                deductions.append(10)
            elif hip_angle > settings.SQUAT_HIP_ANGLE_MAX:
                feedback.append("Squat deeper - aim for 90-degree hip angle")
                deductions.append(15)
            else:
                feedback.append("✓ Good squat depth")

        # Check knee alignment
        if knee_angle < settings.SQUAT_KNEE_ANGLE_MIN:
            feedback.append("Knees too bent - spread them wider")
            deductions.append(10)
        elif knee_angle > settings.SQUAT_KNEE_ANGLE_MAX + 10:
            feedback.append("Keep knees bent more")
            deductions.append(5)
        else:
            feedback.append("✓ Knee angle is good")

        # Check if knees go past toes (approximate)
        if left_knee["pixel_x"] > left_ankle["pixel_x"] + 50:
            feedback.append("Left knee is too far forward")
            deductions.append(15)
        if right_knee["pixel_x"] < right_ankle["pixel_x"] - 50:
            feedback.append("Right knee is too far forward")
            deductions.append(15)

        # Check back straightness (hip-shoulder vertical alignment)
        mid_hip_x = (left_hip["pixel_x"] + right_hip["pixel_x"]) / 2
        mid_shoulder_x = (left_shoulder["pixel_x"] + right_shoulder["pixel_x"]) / 2
        lean = abs(mid_hip_x - mid_shoulder_x)

        if lean > 80:
            feedback.append("Keep your back straight - you're leaning too much")
            deductions.append(10)
        else:
            feedback.append("✓ Back alignment is good")

        # Calculate form score
        total_deduction = sum(deductions)
        form_score = max(0, 100 - total_deduction)

        return {
            "exercise": "squat",
            "form_score": form_score,
            "is_valid": form_score >= settings.FORM_SCORE_THRESHOLD,
            "angles": {
                "hip_angle": round(hip_angle, 1),
                "knee_angle": round(knee_angle, 1),
            },
            "feedback": feedback,
            "rep_phase": rep_phase,
        }

    def _analyze_pushup(self, landmarks: List[Dict], rep_phase: Optional[str]) -> Dict:
        """Analyze push-up form"""
        feedback = []
        deductions = []

        # Get key landmarks
        left_shoulder = self._get_landmark(landmarks, "left_shoulder")
        right_shoulder = self._get_landmark(landmarks, "right_shoulder")
        left_elbow = self._get_landmark(landmarks, "left_elbow")
        right_elbow = self._get_landmark(landmarks, "right_elbow")
        left_wrist = self._get_landmark(landmarks, "left_wrist")
        right_wrist = self._get_landmark(landmarks, "right_wrist")
        left_hip = self._get_landmark(landmarks, "left_hip")
        right_hip = self._get_landmark(landmarks, "right_hip")

        if not all([left_shoulder, right_shoulder, left_elbow, right_elbow, left_wrist, right_wrist]):
            return {
                "exercise": "pushup",
                "form_score": 0,
                "is_valid": False,
                "error": "Could not detect all required landmarks",
                "feedback": ["Make sure your upper body is visible"],
            }

        # Calculate elbow angles
        left_elbow_angle = self._calculate_angle_from_landmarks(
            left_shoulder, left_elbow, left_wrist
        )
        right_elbow_angle = self._calculate_angle_from_landmarks(
            right_shoulder, right_elbow, right_wrist
        )
        elbow_angle = (left_elbow_angle + right_elbow_angle) / 2

        # Check elbow angle (down position)
        if rep_phase == "down" or rep_phase is None:
            if elbow_angle < settings.PUSHUP_ELBOW_ANGLE_MIN:
                feedback.append("Going too low - maintain control")
                deductions.append(5)
            elif elbow_angle > settings.PUSHUP_ELBOW_ANGLE_MAX + 20:
                feedback.append("Go lower - aim for 90-degree elbows")
                deductions.append(15)
            else:
                feedback.append("✓ Good depth")

        # Check body alignment (plank position)
        if left_shoulder and left_hip:
            shoulder_hip_y_diff = abs(left_shoulder["pixel_y"] - left_hip["pixel_y"])
            # In pushup, shoulders should be roughly above hips (vertical alignment)
            if shoulder_hip_y_diff < 50:
                feedback.append("Hips are sagging - engage your core")
                deductions.append(15)
            elif shoulder_hip_y_diff > 200:
                feedback.append("Hips are too high - keep body straight")
                deductions.append(10)
            else:
                feedback.append("✓ Body alignment is good")

        # Check hand width (approximate)
        hand_width = abs(left_wrist["pixel_x"] - right_wrist["pixel_x"])
        shoulder_width = abs(left_shoulder["pixel_x"] - right_shoulder["pixel_x"])

        if hand_width < shoulder_width * 0.8:
            feedback.append("Hands too close - widen your hand position")
            deductions.append(5)
        elif hand_width > shoulder_width * 1.5:
            feedback.append("Hands too wide - bring them closer")
            deductions.append(5)
        else:
            feedback.append("✓ Hand width is correct")

        # Calculate form score
        total_deduction = sum(deductions)
        form_score = max(0, 100 - total_deduction)

        return {
            "exercise": "pushup",
            "form_score": form_score,
            "is_valid": form_score >= settings.FORM_SCORE_THRESHOLD,
            "angles": {
                "elbow_angle": round(elbow_angle, 1),
            },
            "feedback": feedback,
            "rep_phase": rep_phase,
        }

    def _analyze_deadlift(self, landmarks: List[Dict], rep_phase: Optional[str]) -> Dict:
        """Analyze deadlift form"""
        feedback = []
        deductions = []

        # Get key landmarks
        left_shoulder = self._get_landmark(landmarks, "left_shoulder")
        left_hip = self._get_landmark(landmarks, "left_hip")
        left_knee = self._get_landmark(landmarks, "left_knee")
        left_ankle = self._get_landmark(landmarks, "left_ankle")

        if not all([left_shoulder, left_hip, left_knee, left_ankle]):
            return {
                "exercise": "deadlift",
                "form_score": 0,
                "is_valid": False,
                "error": "Could not detect all required landmarks",
                "feedback": ["Make sure your side profile is visible"],
            }

        # Calculate hip angle
        hip_angle = self._calculate_angle_from_landmarks(
            left_shoulder, left_hip, left_knee
        )

        # Check starting position (hip hinge)
        if rep_phase == "down" or rep_phase is None:
            if hip_angle < settings.DEADLIFT_HIP_ANGLE_MIN:
                feedback.append("Hinge at hips more - you're squatting too much")
                deductions.append(15)
            elif hip_angle > settings.DEADLIFT_HIP_ANGLE_MAX:
                feedback.append("Lower your hips slightly")
                deductions.append(5)
            else:
                feedback.append("✓ Hip hinge is correct")

        # Check back straightness
        # Shoulder should be roughly above hip (X-coordinate)
        back_lean = abs(left_shoulder["pixel_x"] - left_hip["pixel_x"])
        if back_lean > 100:
            feedback.append("Keep back straight - avoid rounding")
            deductions.append(20)  # Critical for deadlift
        else:
            feedback.append("✓ Back is straight")

        # Calculate form score
        total_deduction = sum(deductions)
        form_score = max(0, 100 - total_deduction)

        return {
            "exercise": "deadlift",
            "form_score": form_score,
            "is_valid": form_score >= settings.FORM_SCORE_THRESHOLD,
            "angles": {
                "hip_angle": round(hip_angle, 1),
            },
            "feedback": feedback,
            "rep_phase": rep_phase,
        }

    def _analyze_plank(self, landmarks: List[Dict], rep_phase: Optional[str]) -> Dict:
        """Analyze plank form"""
        feedback = []
        deductions = []

        # Get key landmarks
        left_shoulder = self._get_landmark(landmarks, "left_shoulder")
        left_hip = self._get_landmark(landmarks, "left_hip")
        left_ankle = self._get_landmark(landmarks, "left_ankle")

        if not all([left_shoulder, left_hip, left_ankle]):
            return {
                "exercise": "plank",
                "form_score": 0,
                "is_valid": False,
                "error": "Could not detect all required landmarks",
                "feedback": ["Make sure your full body is visible from the side"],
            }

        # Calculate body angle (should be straight line)
        body_angle = self._calculate_angle_from_landmarks(
            left_shoulder, left_hip, left_ankle
        )

        # Ideal plank: ~180 degrees (straight line)
        if body_angle < 160:
            feedback.append("Hips are sagging - engage your core")
            deductions.append(20)
        elif body_angle > 190:
            feedback.append("Hips too high - lower them to form a straight line")
            deductions.append(15)
        else:
            feedback.append("✓ Perfect plank position")

        # Calculate form score
        total_deduction = sum(deductions)
        form_score = max(0, 100 - total_deduction)

        return {
            "exercise": "plank",
            "form_score": form_score,
            "is_valid": form_score >= settings.FORM_SCORE_THRESHOLD,
            "angles": {
                "body_angle": round(body_angle, 1),
            },
            "feedback": feedback,
            "rep_phase": "hold",
        }

    def _get_landmark(self, landmarks: List[Dict], name: str) -> Optional[Dict]:
        """Get landmark by name"""
        for landmark in landmarks:
            if landmark["name"] == name:
                return landmark
        return None

    def _calculate_angle_from_landmarks(
        self,
        landmark1: Dict,
        landmark2: Dict,
        landmark3: Dict,
    ) -> float:
        """Calculate angle between three landmarks"""
        p1 = np.array([landmark1["x"], landmark1["y"], landmark1["z"]])
        p2 = np.array([landmark2["x"], landmark2["y"], landmark2["z"]])
        p3 = np.array([landmark3["x"], landmark3["y"], landmark3["z"]])

        # Vectors
        v1 = p1 - p2
        v2 = p3 - p2

        # Angle
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)

        return np.degrees(angle)
