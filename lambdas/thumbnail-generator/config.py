"""Configuration for Thumbnail Generator Lambda."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Lambda configuration settings."""

    aws_region: str = "ap-northeast-2"
    s3_bucket: str = "gympt-videos"
    thumbnail_width: int = 480
    thumbnail_height: int = 270
    thumbnail_quality: int = 85
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
