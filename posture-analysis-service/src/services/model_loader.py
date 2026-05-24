"""
Model loading and initialization
"""
from typing import Dict
from ..models.pose_estimator import PoseEstimator
from ..services.form_analyzer import FormAnalyzer
from ..config.settings import settings


async def load_models() -> Dict:
    """
    Load ML models on startup

    Returns:
        Dict containing loaded models
    """
    print("Initializing Pose Estimator...")
    pose_estimator = PoseEstimator(
        model_complexity=settings.MEDIAPIPE_MODEL_COMPLEXITY,
        min_detection_confidence=settings.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=settings.MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
    )

    print("Initializing Form Analyzer...")
    form_analyzer = FormAnalyzer()

    print("All models loaded successfully")

    return {
        "pose_estimator": pose_estimator,
        "form_analyzer": form_analyzer,
    }
