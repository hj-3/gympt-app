"""Configuration for Report Generator Lambda."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Lambda configuration settings."""

    aws_region: str = "ap-northeast-2"
    dynamodb_table_prefix: str = "gympt-local"
    s3_bucket: str = "gympt-reports"
    notification_queue_url: str = ""
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    enable_bedrock_mock: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
