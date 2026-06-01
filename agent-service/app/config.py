from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration using Pydantic Settings."""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # Application
    app_env: str = "local"
    service_name: str = "agent-service"
    log_level: str = "INFO"
    
    # AWS
    aws_region: str = "ap-northeast-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Bedrock
    bedrock_region: str = "us-west-2"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_agent_id: Optional[str] = None
    bedrock_agent_alias_id: Optional[str] = None
    bedrock_knowledge_base_id: Optional[str] = None
    enable_bedrock_mock: bool = False  # Set ENABLE_BEDROCK_MOCK=true in .env for local development
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_cache_ttl: int = 3600  # 1 hour
    
    # DynamoDB
    dynamodb_endpoint_url: Optional[str] = None
    dynamodb_agent_interactions_table: str = "gympt-agent-interactions-local"
    
    # SQS
    sqs_endpoint_url: Optional[str] = None
    sqs_agent_task_queue_url: Optional[str] = None
    
    # Backend API
    backend_api_base_url: str = "http://localhost:8080"
    backend_api_timeout: int = 30
    internal_api_token: Optional[str] = None

    # Cache Configuration
    cache_ttl_seconds: int = 3600  # 1 hour default

    # Retry Configuration
    max_retries: int = 3
    backoff_factor: int = 2

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 30
    
    @property
    def is_local(self) -> bool:
        return self.app_env == "local"
    
    @property
    def is_dev(self) -> bool:
        return self.app_env == "dev"
    
    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"
    
    @property
    def should_use_bedrock(self) -> bool:
        """Determine if real Bedrock should be used."""
        return not self.enable_bedrock_mock and self.bedrock_agent_id is not None


settings = Settings()
