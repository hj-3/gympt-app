"""Configuration settings for KVS Consumer Service."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # AWS Configuration
    aws_region: str = "ap-northeast-2"
    kvs_channel_prefix: str = "prod-gympt"

    # Posture Analysis Service
    posture_analysis_url: str = "http://posture-analysis-service:8002/api/v1"

    # Redis Configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Service Configuration
    service_name: str = "kvs-consumer-service"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # Frame Processing
    frame_sample_rate: int = 10  # Process every Nth frame
    max_frame_queue_size: int = 100

    # WebRTC Configuration
    ice_server_ttl: int = 300  # ICE server config TTL in seconds

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
