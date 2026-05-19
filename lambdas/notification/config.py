"""Configuration for Notification Lambda."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Lambda configuration settings."""

    aws_region: str = "ap-northeast-2"
    enable_slack: bool = False
    enable_email: bool = False
    enable_push: bool = False
    slack_webhook_url: str = ""
    sns_email_topic: str = ""
    sns_push_topic: str = ""
    log_level: str = "INFO"

    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 1  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
