"""Configuration for Posture Event Processor Lambda."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Lambda configuration settings."""

    aws_region: str = "ap-northeast-2"
    dynamodb_table_prefix: str = "gympt-local"
    cloudwatch_namespace: str = "GymPT/PostureAnalysis"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
