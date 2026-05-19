"""
Remediation Worker Configuration
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Service Identity
    SERVICE_NAME: str = "remediation-worker"

    # Environment
    APP_ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    # AWS Configuration
    AWS_REGION: str = "ap-northeast-2"

    # Check Interval
    CHECK_INTERVAL_SECONDS: int = 60
    REMEDIATION_ENABLED: bool = True

    # Service URLs
    BACKEND_API_BASE_URL: str = "http://localhost:8080"
    PROMETHEUS_BASE_URL: str = "http://localhost:9090"

    # Health Check Thresholds
    CPU_THRESHOLD_PERCENT: float = 80.0
    MEMORY_THRESHOLD_PERCENT: float = 85.0
    DISK_THRESHOLD_PERCENT: float = 90.0
    POD_RESTART_THRESHOLD: int = 5

    # Remediation Actions
    ENABLE_AUTO_RESTART: bool = False
    ENABLE_AUTO_SCALE: bool = True
    ENABLE_ALERT_ONLY: bool = True

    # Kubernetes
    KUBECONFIG_PATH: Optional[str] = None
    KUBE_NAMESPACE: str = "gympt-dev"

    # Slack Notifications
    SLACK_WEBHOOK_URL: Optional[str] = None

    # Monitoring
    PROMETHEUS_ENABLED: bool = True

    @property
    def is_local(self) -> bool:
        return self.APP_ENV == "local"

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "dev"

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "prod"

    @property
    def is_remediation_enabled(self) -> bool:
        """Check if remediation is enabled"""
        return self.REMEDIATION_ENABLED and not self.ENABLE_ALERT_ONLY

    def validate_required_for_env(self):
        """Validate configuration"""
        if self.is_prod and self.ENABLE_AUTO_RESTART:
            raise ValueError("ENABLE_AUTO_RESTART should not be true in production")

        if not self.is_local and not self.SLACK_WEBHOOK_URL:
            raise ValueError("SLACK_WEBHOOK_URL required for dev/prod")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()

    if not settings.is_local:
        settings.validate_required_for_env()

    return settings


settings = get_settings()
