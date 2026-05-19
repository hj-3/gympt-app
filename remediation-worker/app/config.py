from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application settings
    environment: str = "dev"
    log_level: str = "INFO"
    dry_run: bool = False

    # Slack settings
    slack_webhook_url: Optional[str] = None

    # Argo CD settings
    argocd_server: str = "argocd-server.argocd.svc.cluster.local:443"
    argocd_auth_token: Optional[str] = None
    argocd_insecure: bool = True

    # AWS settings
    aws_region: str = "ap-northeast-2"
    eks_cluster_name: str = "gympt-dev-eks"

    # Action limits
    max_restarts_per_hour: int = 3
    max_scale_ups_per_hour: int = 5
    max_rollbacks_per_hour: int = 2
    cooldown_period: int = 300  # seconds

    # Excluded namespaces and deployments
    excluded_namespaces: list[str] = [
        "kube-system",
        "kube-public",
        "kube-node-lease",
        "argocd",
        "monitoring"
    ]
    excluded_deployments: list[str] = [
        "kube-prometheus-stack",
        "argocd-server",
        "argocd-repo-server",
        "remediation-worker"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
