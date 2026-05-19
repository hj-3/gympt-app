"""Configuration for Recommendation Update Lambda."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Lambda configuration settings."""

    aws_region: str = "ap-northeast-2"
    dynamodb_table_prefix: str = "gympt-local"
    backend_api_url: str = "http://localhost:8000"
    backend_api_key: str = ""
    log_level: str = "INFO"

    # Analysis thresholds
    min_sessions_for_adjustment: int = 3
    excellent_score_threshold: float = 8.5
    poor_score_threshold: float = 6.0
    high_completion_threshold: float = 0.9
    low_completion_threshold: float = 0.5

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
