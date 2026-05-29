from fastapi import FastAPI, Request, Response
from app.config import settings
from app.logger import setup_logger
from app.models import (
    AlertmanagerWebhook,
    CloudWatchEvent,
    RemediationAction
)
from app.remediation_engine import RemediationEngine
from app.metrics import get_metrics, webhook_requests_total
import yaml
from pathlib import Path

logger = setup_logger(__name__, settings.log_level)

app = FastAPI(
    title="Remediation Worker",
    description="Automated remediation service for Kubernetes",
    version="1.0.0"
)

# Load alert rules
ALERT_RULES = {}
rules_path = Path("/etc/remediation/alert-rules.yaml")
if rules_path.exists():
    with open(rules_path) as f:
        alert_rules_config = yaml.safe_load(f)
        ALERT_RULES = {rule["alertName"]: rule for rule in alert_rules_config.get("rules", [])}
    logger.info(f"Loaded {len(ALERT_RULES)} alert rules")
else:
    logger.warning("Alert rules file not found, using empty rules")

remediation_engine = RemediationEngine()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "environment": settings.environment}


@app.get("/ready")
async def ready():
    """Readiness check endpoint"""
    return {"status": "ready"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)


@app.post("/webhook/alert")
async def alertmanager_webhook(webhook: AlertmanagerWebhook, request: Request):
    """Receive webhook from Alertmanager"""
    webhook_requests_total.labels(source="alertmanager", status="received").inc()

    logger.info(
        f"Received Alertmanager webhook: {webhook.groupKey}",
        extra={
            "groupKey": webhook.groupKey,
            "status": webhook.status,
            "alertCount": len(webhook.alerts)
        }
    )

    # Process each alert
    for alert in webhook.alerts:
        if alert.status != "firing":
            logger.info(f"Skipping non-firing alert: {alert.labels.get('alertname')}")
            continue

        alert_name = alert.labels.get("alertname")
        if not alert_name:
            logger.warning("Alert missing alertname label, skipping")
            continue

        # Look up remediation rule
        rule = ALERT_RULES.get(alert_name)
        if not rule:
            logger.info(f"No remediation rule for alert: {alert_name}")
            webhook_requests_total.labels(source="alertmanager", status="no_rule").inc()
            continue

        # Build remediation action
        action = RemediationAction(
            action_type=rule["action"],
            namespace=rule["params"].get("namespace", alert.labels.get("namespace", "default")),
            target=rule["params"].get("deployment", alert.labels.get("deployment", "unknown")),
            params=rule["params"],
            dry_run=rule.get("dryRun", False),
            notify_slack=rule.get("notifySlack", True),
            cooldown=rule.get("cooldown", settings.cooldown_period)
        )

        logger.info(
            f"Executing remediation for alert {alert_name}",
            extra={
                "alert": alert_name,
                "action": action.action_type,
                "target": action.target,
                "namespace": action.namespace
            }
        )

        # Execute remediation
        result = await remediation_engine.execute_action(
            action=action,
            alert_name=alert_name,
            severity=rule.get("severity", "info")
        )

        if result.success:
            logger.info(
                f"Remediation successful for alert {alert_name}: {result.message}",
                extra={"alert": alert_name, "result": result.message}
            )
            webhook_requests_total.labels(source="alertmanager", status="success").inc()
        else:
            logger.error(
                f"Remediation failed for alert {alert_name}: {result.message}",
                extra={"alert": alert_name, "error": result.error}
            )
            webhook_requests_total.labels(source="alertmanager", status="failure").inc()

    return {"status": "processed", "alerts": len(webhook.alerts)}


@app.post("/webhook/cloudwatch")
async def cloudwatch_webhook(event: CloudWatchEvent, request: Request):
    """Receive webhook from AWS CloudWatch Events"""
    webhook_requests_total.labels(source="cloudwatch", status="received").inc()

    logger.info(
        f"Received CloudWatch event: {event.detail_type}",
        extra={
            "id": event.id,
            "detail_type": event.detail_type,
            "source": event.source
        }
    )

    # Handle different CloudWatch event types
    # This is a placeholder - implement based on your CloudWatch Events configuration
    logger.info("CloudWatch event processing not yet implemented")

    return {"status": "received", "id": event.id}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "remediation-worker",
        "version": "1.0.0",
        "environment": settings.environment,
        "dry_run": settings.dry_run,
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "metrics": "/metrics",
            "alertmanager_webhook": "/webhook/alert",
            "cloudwatch_webhook": "/webhook/cloudwatch"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
