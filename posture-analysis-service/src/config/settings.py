"""
Configuration settings for Posture Analysis Service
"""
import os
from typing import List


class Settings:
    """Application settings"""

    # Service info
    SERVICE_NAME = "GYMPT Posture Analysis Service"
    VERSION = "1.0.0"
    ENV = os.getenv("ENV", "local")

    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8002"))

    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,https://g2mpt.com,https://api.g2mpt.com"
    ).split(",")

    # GPU
    GPU_ENABLED = os.getenv("GPU_ENABLED", "false").lower() == "true"

    # MediaPipe settings
    MEDIAPIPE_MODEL_COMPLEXITY = int(os.getenv("MEDIAPIPE_MODEL_COMPLEXITY", "1"))  # 0, 1, 2
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE = float(os.getenv("MEDIAPIPE_MIN_DETECTION_CONFIDENCE", "0.5"))
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE = float(os.getenv("MEDIAPIPE_MIN_TRACKING_CONFIDENCE", "0.5"))

    # AWS
    AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
    KVS_STREAM_NAME = os.getenv("KVS_STREAM_NAME", "gympt-workout-stream")

    # Backend API
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8080/api/v1")

    # Analysis thresholds
    FORM_SCORE_THRESHOLD = float(os.getenv("FORM_SCORE_THRESHOLD", "70.0"))  # Out of 100
    MIN_CONFIDENCE_THRESHOLD = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.6"))

    # Exercise-specific settings
    SQUAT_HIP_ANGLE_MIN = 80
    SQUAT_HIP_ANGLE_MAX = 100
    SQUAT_KNEE_ANGLE_MIN = 80
    SQUAT_KNEE_ANGLE_MAX = 100

    PUSHUP_ELBOW_ANGLE_MIN = 80
    PUSHUP_ELBOW_ANGLE_MAX = 100

    DEADLIFT_HIP_ANGLE_MIN = 140
    DEADLIFT_HIP_ANGLE_MAX = 160


settings = Settings()
