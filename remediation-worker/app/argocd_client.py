import httpx
from typing import Optional
from app.config import settings
from app.logger import setup_logger
from app.models import RemediationResult

logger = setup_logger(__name__, settings.log_level)


class ArgoCDClient:
    """Argo CD API client for rollback operations"""

    def __init__(self):
        self.server = settings.argocd_server
        self.token = settings.argocd_auth_token
        self.base_url = f"https://{self.server}/api/v1"
        self.verify_ssl = not settings.argocd_insecure

    async def rollback_application(
        self,
        application: str,
        revision_history: int = 1,
        dry_run: bool = False
    ) -> RemediationResult:
        """Rollback an Argo CD application to a previous revision"""
        try:
            if not self.token:
                return RemediationResult(
                    success=False,
                    action_type="rollback_argocd",
                    namespace="argocd",
                    target=application,
                    message="Argo CD auth token not configured",
                    error="Missing ARGOCD_AUTH_TOKEN"
                )

            if dry_run:
                logger.info(
                    f"DRY RUN: Would rollback Argo CD application {application} by {revision_history} revision(s)",
                    extra={"application": application, "revision_history": revision_history}
                )
                return RemediationResult(
                    success=True,
                    action_type="rollback_argocd",
                    namespace="argocd",
                    target=application,
                    message=f"DRY RUN: Would rollback application {application}",
                    dry_run=True
                )

            # Get application details
            app_info = await self._get_application(application)
            if not app_info:
                return RemediationResult(
                    success=False,
                    action_type="rollback_argocd",
                    namespace="argocd",
                    target=application,
                    message=f"Application {application} not found",
                    error="Application not found"
                )

            # Get history
            history = app_info.get("status", {}).get("history", [])
            if len(history) < revision_history + 1:
                return RemediationResult(
                    success=False,
                    action_type="rollback_argocd",
                    namespace="argocd",
                    target=application,
                    message=f"Not enough history to rollback {revision_history} revision(s)",
                    error="Insufficient history"
                )

            # Get target revision (history is sorted newest first)
            target_revision = history[-(revision_history + 1)]["id"]

            # Trigger rollback
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                response = await client.post(
                    f"{self.base_url}/applications/{application}/rollback",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={"id": target_revision}
                )

                if response.status_code == 200:
                    logger.info(
                        f"Successfully triggered rollback for application {application} to revision {target_revision}",
                        extra={"application": application, "revision": target_revision}
                    )
                    return RemediationResult(
                        success=True,
                        action_type="rollback_argocd",
                        namespace="argocd",
                        target=application,
                        message=f"Rolled back to revision {target_revision}"
                    )
                else:
                    error_msg = response.text
                    logger.error(
                        f"Failed to rollback application {application}: {error_msg}",
                        extra={"application": application, "error": error_msg}
                    )
                    return RemediationResult(
                        success=False,
                        action_type="rollback_argocd",
                        namespace="argocd",
                        target=application,
                        message=f"Rollback failed: {error_msg}",
                        error=error_msg
                    )

        except Exception as e:
            logger.error(
                f"Exception during rollback of application {application}: {str(e)}",
                extra={"application": application, "error": str(e)}
            )
            return RemediationResult(
                success=False,
                action_type="rollback_argocd",
                namespace="argocd",
                target=application,
                message=f"Rollback failed with exception: {str(e)}",
                error=str(e)
            )

    async def _get_application(self, application: str) -> Optional[dict]:
        """Get application details from Argo CD"""
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl) as client:
                response = await client.get(
                    f"{self.base_url}/applications/{application}",
                    headers={"Authorization": f"Bearer {self.token}"}
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(
                        f"Failed to get application {application}: {response.text}",
                        extra={"application": application, "status": response.status_code}
                    )
                    return None

        except Exception as e:
            logger.error(
                f"Exception getting application {application}: {str(e)}",
                extra={"application": application, "error": str(e)}
            )
            return None
