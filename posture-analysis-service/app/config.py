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

    # Rep Counter Thresholds
    rep_counter_thresholds: dict = {
        "squat": {
            "down_threshold": 0.15,
            "up_threshold": 0.25,
            "hysteresis": 0.05,
        },
        "pushup": {
            "down_threshold": 0.10,
            "up_threshold": 0.20,
            "hysteresis": 0.03,
        },
        "deadlift": {
            "down_threshold": 0.20,
            "up_threshold": 0.35,
            "hysteresis": 0.05,
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
