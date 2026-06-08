from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration."""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # Application
    app_env: str = "local"
    service_name: str = "posture-analysis-service"
    log_level: str = "INFO"
    
    # Hardware
    enable_gpu: bool = False
    model_type: str = "mediapipe"  # mediapipe (real pose), mock (tests only)
    
    # AWS
    aws_region: str = "ap-northeast-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Kinesis Video Streams
    kvs_signaling_channel_name: Optional[str] = None
    kvs_signaling_channel_arn: Optional[str] = None
    enable_kvs_mock: bool = True
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    
    # DynamoDB
    dynamodb_endpoint_url: Optional[str] = None
    dynamodb_posture_events_table: str = "gympt-posture-events-local"
    
    # S3
    s3_endpoint_url: Optional[str] = None
    s3_media_bucket: str = "gympt-media-local"
    s3_posture_results_prefix: str = "posture-results"
    
    # SQS
    sqs_endpoint_url: Optional[str] = None
    sqs_posture_event_queue_url: Optional[str] = None
    
    # CORS
    cors_origins: str = "http://localhost:3000"

    # Analysis
    frame_processing_interval: float = 0.1  # seconds
    feedback_threshold_score: float = 7.0  # below this, send feedback
    max_websocket_connections: int = 100
    log_interval_seconds: int = 5  # DynamoDB logging interval

    # Rep Counter Thresholds — angle-based (degrees), must match RepCounter.DEFAULT_THRESHOLDS
    rep_counter_thresholds: dict = {
        "squat": {
            "down_threshold": 100,   # knee angle below this → squatting
            "up_threshold":   160,   # knee angle above this → standing
            "hysteresis":      10,
        },
        "lunge": {
            "down_threshold": 100,
            "up_threshold":   160,
            "hysteresis":      10,
        },
        "pushup": {
            "down_threshold":  90,   # elbow angle below this → chest near floor
            "up_threshold":   150,   # elbow angle above this → arms extended
            "hysteresis":      10,
        },
        "deadlift": {
            "down_threshold": 100,   # hip angle below this → bent over
            "up_threshold":   160,   # hip angle above this → standing
            "hysteresis":      10,
        },
        "plank": {
            "down_threshold": 0,
            "up_threshold":   0,
            "hysteresis":     0,
        },
    }
    
    @property
    def is_local(self) -> bool:
        return self.app_env == "local"
    
    @property
    def should_use_gpu(self) -> bool:
        """Check if GPU should be used."""
        if not self.enable_gpu:
            return False
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False


settings = Settings()
