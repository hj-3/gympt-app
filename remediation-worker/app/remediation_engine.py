from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.config import settings
from app.logger import setup_logger
from app.models import RemediationAction, RemediationResult, ActionHistory
from app.kubernetes_client import KubernetesClient
from app.argocd_client import ArgoCDClient
from app.slack_client import SlackClient
from app.metrics import (
    remediation_actions_total,
    remediation_action_duration_seconds,
    remediation_cooldown_blocks,
    remediation_rate_limit_blocks,
    remediation_dry_run_actions,
    active_remediations
)
import time

logger = setup_logger(__name__, settings.log_level)


class RemediationEngine:
    """Core remediation engine with rate limiting and cooldown"""

    def __init__(self):
        self.k8s_client = KubernetesClient()
        self.argocd_client = ArgoCDClient()
        self.slack_client = SlackClient()
        self.action_history: List[ActionHistory] = []
        self.cooldown_cache: Dict[str, datetime] = {}

    async def execute_action(
        self,
        action: RemediationAction,
        alert_name: Optional[str] = None,
        severity: str = "info"
    ) -> RemediationResult:
        """Execute a remediation action with safety checks"""
        start_time = time.time()
        active_remediations.inc()

        try:
            # Check if action is excluded
            if self._is_excluded(action):
                result = RemediationResult(
                    success=False,
                    action_type=action.action_type,
                    namespace=action.namespace,
                    target=action.target,
                    message=f"Action blocked: {action.target} is excluded",
                    error="Target is in excluded list"
                )
                remediation_actions_total.labels(
                    action_type=action.action_type,
                    namespace=action.namespace,
                    status="excluded"
                ).inc()
                return result

            # Check cooldown
            if self._in_cooldown(action):
                result = RemediationResult(
                    success=False,
                    action_type=action.action_type,
                    namespace=action.namespace,
                    target=action.target,
                    message=f"Action blocked by cooldown period",
                    error="Action is in cooldown"
                )
                remediation_cooldown_blocks.labels(
                    action_type=action.action_type,
                    namespace=action.namespace
                ).inc()
                logger.warning(
                    f"Action blocked by cooldown: {action.action_type} for {action.target}",
                    extra={"action": action.action_type, "target": action.target}
                )
                return result

            # Check rate limits
            if not self._check_rate_limit(action):
                result = RemediationResult(
                    success=False,
                    action_type=action.action_type,
                    namespace=action.namespace,
                    target=action.target,
                    message=f"Action blocked by rate limit",
                    error="Rate limit exceeded"
                )
                remediation_rate_limit_blocks.labels(
                    action_type=action.action_type
                ).inc()
                logger.warning(
                    f"Action blocked by rate limit: {action.action_type}",
                    extra={"action": action.action_type}
                )
                return result

            # Override dry_run if globally enabled
            dry_run = action.dry_run or settings.dry_run

            if dry_run:
                remediation_dry_run_actions.labels(
                    action_type=action.action_type,
                    namespace=action.namespace
                ).inc()

            # Execute action based on type
            if action.action_type == "restart_deployment":
                result = self.k8s_client.restart_deployment(
                    namespace=action.namespace,
                    deployment=action.target,
                    grace_period=action.params.get("gracePeriod", 30),
                    dry_run=dry_run
                )

            elif action.action_type == "scale_deployment":
                result = self.k8s_client.scale_deployment(
                    namespace=action.namespace,
                    deployment=action.target,
                    scale_direction=action.params.get("scaleDirection", "up"),
                    target_replicas=action.params.get("targetReplicas", "+1"),
                    max_replicas=action.params.get("maxReplicas", 10),
                    min_replicas=action.params.get("minReplicas", 1),
                    dry_run=dry_run
                )

            elif action.action_type == "rollback_argocd":
                result = await self.argocd_client.rollback_application(
                    application=action.target,
                    revision_history=action.params.get("revisionHistory", 1),
                    dry_run=dry_run
                )

            elif action.action_type == "notify_only":
                result = RemediationResult(
                    success=True,
                    action_type=action.action_type,
                    namespace=action.namespace,
                    target=action.target,
                    message=action.params.get("message", "Notification triggered")
                )

            elif action.action_type == "patch_deployment":
                result = self.k8s_client.patch_deployment(
                    namespace=action.namespace,
                    deployment=action.target,
                    patch=action.params.get("patch", {}),
                    dry_run=dry_run
                )

            else:
                result = RemediationResult(
                    success=False,
                    action_type=action.action_type,
                    namespace=action.namespace,
                    target=action.target,
                    message=f"Unknown action type: {action.action_type}",
                    error="Unknown action type"
                )

            # Record action history
            if result.success and not dry_run:
                self._record_action(action)
                self._set_cooldown(action)

            # Record metrics
            status = "success" if result.success else "failure"
            remediation_actions_total.labels(
                action_type=action.action_type,
                namespace=action.namespace,
                status=status
            ).inc()

            duration = time.time() - start_time
            remediation_action_duration_seconds.labels(
                action_type=action.action_type,
                namespace=action.namespace
            ).observe(duration)

            # Send Slack notification
            if action.notify_slack:
                await self.slack_client.send_notification(result, alert_name, severity)

            return result

        finally:
            active_remediations.dec()

    def _is_excluded(self, action: RemediationAction) -> bool:
        """Check if action target is excluded"""
        if action.namespace in settings.excluded_namespaces:
            return True
        if action.target in settings.excluded_deployments:
            return True
        return False

    def _in_cooldown(self, action: RemediationAction) -> bool:
        """Check if action is in cooldown period"""
        key = f"{action.namespace}:{action.target}:{action.action_type}"
        if key in self.cooldown_cache:
            cooldown_until = self.cooldown_cache[key]
            if datetime.utcnow() < cooldown_until:
                return True
            else:
                del self.cooldown_cache[key]
        return False

    def _set_cooldown(self, action: RemediationAction):
        """Set cooldown for action"""
        key = f"{action.namespace}:{action.target}:{action.action_type}"
        cooldown_until = datetime.utcnow() + timedelta(seconds=action.cooldown)
        self.cooldown_cache[key] = cooldown_until
        logger.info(
            f"Set cooldown for {key} until {cooldown_until}",
            extra={"key": key, "cooldown_until": str(cooldown_until)}
        )

    def _check_rate_limit(self, action: RemediationAction) -> bool:
        """Check if action exceeds rate limits"""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)

        # Clean old history
        self.action_history = [
            h for h in self.action_history
            if h.timestamp > one_hour_ago
        ]

        # Count actions by type in last hour
        if action.action_type == "restart_deployment":
            count = sum(
                1 for h in self.action_history
                if h.action_type == "restart_deployment"
            )
            limit = settings.max_restarts_per_hour
        elif action.action_type == "scale_deployment":
            count = sum(
                1 for h in self.action_history
                if h.action_type == "scale_deployment"
            )
            limit = settings.max_scale_ups_per_hour
        elif action.action_type == "rollback_argocd":
            count = sum(
                1 for h in self.action_history
                if h.action_type == "rollback_argocd"
            )
            limit = settings.max_rollbacks_per_hour
        else:
            # No rate limit for other actions
            return True

        return count < limit

    def _record_action(self, action: RemediationAction):
        """Record action in history"""
        self.action_history.append(
            ActionHistory(
                action_type=action.action_type,
                namespace=action.namespace,
                target=action.target,
                timestamp=datetime.utcnow()
            )
        )
        logger.info(
            f"Recorded action: {action.action_type} for {action.target}",
            extra={
                "action": action.action_type,
                "namespace": action.namespace,
                "target": action.target
            }
        )
