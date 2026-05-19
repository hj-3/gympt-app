"""Configuration for Export Lambda."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Lambda configuration settings."""

    aws_region: str = "ap-northeast-2"
    dynamodb_table_prefix: str = "gympt-local"
    s3_bucket: str = "gympt-exports"
    presigned_url_expiry: int = 3600  # 1 hour in seconds
    default_date_range_days: int = 30
    log_level: str = "INFO"

    # Supported export formats
    supported_formats: list = ["csv", "json"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
