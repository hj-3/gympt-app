"""
Configuration settings for Report Service
"""
import os
from typing import List


class Settings:
    """Application settings"""

    # Service info
    SERVICE_NAME = "GYMPT Report Service"
    VERSION = "1.0.0"
    ENV = os.getenv("ENV", "local")

    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8003"))

    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,https://g2mpt.com,https://api.g2mpt.com"
    ).split(",")

    # AWS
    AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
    S3_BUCKET_REPORTS = os.getenv("S3_BUCKET_REPORTS", "gympt-workout-reports-prod")
    S3_PRESIGNED_URL_EXPIRY = int(os.getenv("S3_PRESIGNED_URL_EXPIRY", "3600"))  # 1 hour

    # DynamoDB
    DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "gympt-prod")
    DYNAMODB_WORKOUT_SESSIONS_TABLE = f"{DYNAMODB_TABLE_PREFIX}-workout-sessions"

    # Backend API
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8080/api/v1")

    # Report settings
    REPORT_TITLE_FONT_SIZE = 24
    REPORT_HEADING_FONT_SIZE = 16
    REPORT_BODY_FONT_SIZE = 12
    CHART_WIDTH = 500
    CHART_HEIGHT = 300


settings = Settings()
