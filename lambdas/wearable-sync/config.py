"""Configuration for Wearable Sync Lambda."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Lambda configuration settings."""

    aws_region: str = "ap-northeast-2"
    dynamodb_table_prefix: str = "gympt-local"
    supported_devices: List[str] = ["APPLE_WATCH", "FITBIT", "GARMIN"]
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
