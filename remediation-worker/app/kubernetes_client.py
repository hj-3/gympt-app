from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import Dict, Any
from app.config import settings
from app.logger import setup_logger
from app.models import RemediationResult
import time

logger = setup_logger(__name__, settings.log_level)


class KubernetesClient:
    """Kubernetes API client for remediation actions"""

    def __init__(self):
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes configuration")
        except config.ConfigException:
            config.load_kube_config()
            logger.info("Loaded kubeconfig from local filesystem")

        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.batch_v1 = client.BatchV1Api()

    def restart_deployment(
        self,
        namespace: str,
        deployment: str,
        grace_period: int = 30,
        dry_run: bool = False
    ) -> RemediationResult:
        """Restart a deployment by adding a restart annotation"""
        try:
            if self._is_excluded(namespace, deployment):
                return RemediationResult(
                    success=False,
                    action_type="restart_deployment",
                    namespace=namespace,
                    target=deployment,
                    message=f"Deployment {deployment} in namespace {namespace} is excluded",
                    error="Deployment is in excluded list"
                )

            if dry_run:
                logger.info(
                    f"DRY RUN: Would restart deployment {deployment} in namespace {namespace}",
                    extra={"namespace": namespace, "deployment": deployment}
                )
                return RemediationResult(
                    success=True,
                    action_type="restart_deployment",
                    namespace=namespace,
                    target=deployment,
                    message=f"DRY RUN: Would restart deployment {deployment}",
                    dry_run=True
                )

            # Patch deployment with restart annotation
            patch_body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubectl.kubernetes.io/restartedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                            }
                        }
                    }
                }
            }

            self.apps_v1.patch_namespaced_deployment(
                name=deployment,
                namespace=namespace,
                body=patch_body
            )

            logger.info(
                f"Successfully triggered restart for deployment {deployment} in namespace {namespace}",
                extra={"namespace": namespace, "deployment": deployment}
            )

            return RemediationResult(
                success=True,
                action_type="restart_deployment",
                namespace=namespace,
                target=deployment,
                message=f"Successfully restarted deployment {deployment}"
            )

        except ApiException as e:
            logger.error(
                f"Failed to restart deployment {deployment}: {e.reason}",
                extra={"namespace": namespace, "deployment": deployment, "error": str(e)}
            )
            return RemediationResult(
                success=False,
                action_type="restart_deployment",
                namespace=namespace,
                target=deployment,
                message=f"Failed to restart deployment: {e.reason}",
                error=str(e)
            )

    def scale_deployment(
        self,
        namespace: str,
        deployment: str,
        scale_direction: str,
        target_replicas: str,
        max_replicas: int = 10,
        min_replicas: int = 1,
        dry_run: bool = False
    ) -> RemediationResult:
        """Scale a deployment up or down"""
        try:
            if self._is_excluded(namespace, deployment):
                return RemediationResult(
                    success=False,
                    action_type="scale_deployment",
                    namespace=namespace,
                    target=deployment,
                    message=f"Deployment {deployment} in namespace {namespace} is excluded",
                    error="Deployment is in excluded list"
                )

            # Get current replicas
            dep = self.apps_v1.read_namespaced_deployment(name=deployment, namespace=namespace)
            current_replicas = dep.spec.replicas or 0

            # Calculate new replicas
            if target_replicas.startswith("+"):
                new_replicas = current_replicas + int(target_replicas[1:])
            elif target_replicas.startswith("-"):
                new_replicas = current_replicas - int(target_replicas[1:])
            else:
                new_replicas = int(target_replicas)

            # Apply limits
            new_replicas = max(min_replicas, min(new_replicas, max_replicas))

            if new_replicas == current_replicas:
                return RemediationResult(
                    success=True,
                    action_type="scale_deployment",
                    namespace=namespace,
                    target=deployment,
                    message=f"Deployment already at target replicas ({current_replicas})"
                )

            if dry_run:
                logger.info(
                    f"DRY RUN: Would scale deployment {deployment} from {current_replicas} to {new_replicas}",
                    extra={"namespace": namespace, "deployment": deployment, "current": current_replicas, "target": new_replicas}
                )
                return RemediationResult(
                    success=True,
                    action_type="scale_deployment",
                    namespace=namespace,
                    target=deployment,
                    message=f"DRY RUN: Would scale from {current_replicas} to {new_replicas}",
                    dry_run=True
                )

            # Scale deployment
            dep.spec.replicas = new_replicas
            self.apps_v1.patch_namespaced_deployment_scale(
                name=deployment,
                namespace=namespace,
                body={"spec": {"replicas": new_replicas}}
            )

            logger.info(
                f"Successfully scaled deployment {deployment} from {current_replicas} to {new_replicas}",
                extra={"namespace": namespace, "deployment": deployment, "from": current_replicas, "to": new_replicas}
            )

            return RemediationResult(
                success=True,
                action_type="scale_deployment",
                namespace=namespace,
                target=deployment,
                message=f"Scaled deployment from {current_replicas} to {new_replicas} replicas"
            )

        except ApiException as e:
            logger.error(
                f"Failed to scale deployment {deployment}: {e.reason}",
                extra={"namespace": namespace, "deployment": deployment, "error": str(e)}
            )
            return RemediationResult(
                success=False,
                action_type="scale_deployment",
                namespace=namespace,
                target=deployment,
                message=f"Failed to scale deployment: {e.reason}",
                error=str(e)
            )

    def patch_deployment(
        self,
        namespace: str,
        deployment: str,
        patch: Dict[str, Any],
        dry_run: bool = False
    ) -> RemediationResult:
        """Apply a JSON patch to a deployment"""
        try:
            if self._is_excluded(namespace, deployment):
                return RemediationResult(
                    success=False,
                    action_type="patch_deployment",
                    namespace=namespace,
                    target=deployment,
                    message=f"Deployment {deployment} in namespace {namespace} is excluded",
                    error="Deployment is in excluded list"
                )

            if dry_run:
                logger.info(
                    f"DRY RUN: Would patch deployment {deployment}",
                    extra={"namespace": namespace, "deployment": deployment, "patch": patch}
                )
                return RemediationResult(
                    success=True,
                    action_type="patch_deployment",
                    namespace=namespace,
                    target=deployment,
                    message="DRY RUN: Would apply patch to deployment",
                    dry_run=True
                )

            self.apps_v1.patch_namespaced_deployment(
                name=deployment,
                namespace=namespace,
                body=patch
            )

            logger.info(
                f"Successfully patched deployment {deployment}",
                extra={"namespace": namespace, "deployment": deployment}
            )

            return RemediationResult(
                success=True,
                action_type="patch_deployment",
                namespace=namespace,
                target=deployment,
                message=f"Successfully patched deployment {deployment}"
            )

        except ApiException as e:
            logger.error(
                f"Failed to patch deployment {deployment}: {e.reason}",
                extra={"namespace": namespace, "deployment": deployment, "error": str(e)}
            )
            return RemediationResult(
                success=False,
                action_type="patch_deployment",
                namespace=namespace,
                target=deployment,
                message=f"Failed to patch deployment: {e.reason}",
                error=str(e)
            )

    def _is_excluded(self, namespace: str, deployment: str) -> bool:
        """Check if namespace or deployment is excluded"""
        if namespace in settings.excluded_namespaces:
            return True
        if deployment in settings.excluded_deployments:
            return True
        return False
