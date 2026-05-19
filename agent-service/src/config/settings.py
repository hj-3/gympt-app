"""
Application settings using Pydantic Settings
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    SERVICE_NAME: str = "gympt-agent-service"
    VERSION: str = "0.1.0"
    ENV: str = "local"
    PROJECT_NAME: str = "gympt"

    # AWS
    AWS_REGION: str = "ap-northeast-2"
    AWS_ACCOUNT_ID: str = ""

    # Bedrock
    BEDROCK_AGENT_ID: str = ""
    BEDROCK_AGENT_ALIAS_ID: str = ""
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    BEDROCK_REGION: str = "us-west-2"

    # Agent Configuration
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 60

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Redis (for caching agent responses)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # Database (if needed for agent state)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "gympt"
    DB_USER: str = "gympt_user"
    DB_PASSWORD: str = "changeme"


settings = Settings()
