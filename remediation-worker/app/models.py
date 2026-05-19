from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class AlertmanagerAlert(BaseModel):
    """Individual alert from Alertmanager"""
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: Optional[str] = None
    fingerprint: Optional[str] = None


class AlertmanagerWebhook(BaseModel):
    """Alertmanager webhook payload"""
    version: str = "4"
    groupKey: str
    truncatedAlerts: int = 0
    status: str
    receiver: str
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: str
    alerts: list[AlertmanagerAlert]


class CloudWatchEvent(BaseModel):
    """AWS CloudWatch Event payload"""
    version: str
    id: str
    detail_type: str = Field(alias="detail-type")
    source: str
    account: str
    time: str
    region: str
    resources: list[str]
    detail: Dict[str, Any]


class RemediationAction(BaseModel):
    """Remediation action to execute"""
    action_type: Literal[
        "restart_deployment",
        "scale_deployment",
        "rollback_argocd",
        "notify_only",
        "run_job",
        "patch_deployment"
    ]
    namespace: str
    target: str  # deployment name, argocd app name, etc.
    params: Dict[str, Any] = {}
    dry_run: bool = False
    notify_slack: bool = True
    cooldown: int = 300  # seconds


class RemediationResult(BaseModel):
    """Result of a remediation action"""
    success: bool
    action_type: str
    namespace: str
    target: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dry_run: bool = False
    error: Optional[str] = None


class ActionHistory(BaseModel):
    """History entry for action rate limiting"""
    action_type: str
    namespace: str
    target: str
    timestamp: datetime
