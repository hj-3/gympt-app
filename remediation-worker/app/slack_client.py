import httpx
from typing import Optional
from app.config import settings
from app.logger import setup_logger
from app.models import RemediationResult

logger = setup_logger(__name__, settings.log_level)


class SlackClient:
    """Slack notification client"""

    def __init__(self):
        self.webhook_url = settings.slack_webhook_url

    async def send_notification(
        self,
        result: RemediationResult,
        alert_name: Optional[str] = None,
        severity: str = "info"
    ):
        """Send notification to Slack"""
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured, skipping notification")
            return

        color = self._get_color(severity, result.success)
        emoji = self._get_emoji(result.success, result.dry_run)

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Remediation Action: {result.action_type}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Status:*\n{':white_check_mark: Success' if result.success else ':x: Failed'}"},
                    {"type": "mrkdwn", "text": f"*Target:*\n`{result.target}`"},
                    {"type": "mrkdwn", "text": f"*Namespace:*\n`{result.namespace}`"},
                    {"type": "mrkdwn", "text": f"*Action:*\n{result.action_type}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Message:*\n{result.message}"
                }
            }
        ]

        if alert_name:
            blocks.insert(1, {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Alert:*\n{alert_name}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"}
                ]
            })

        if result.error:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{result.error}```"
                }
            })

        if result.dry_run:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": ":information_source: This was a *DRY RUN* - no actual changes were made"
                    }
                ]
            })

        payload = {
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload)
                if response.status_code == 200:
                    logger.info(f"Sent Slack notification for {result.action_type}")
                else:
                    logger.error(f"Failed to send Slack notification: {response.text}")

        except Exception as e:
            logger.error(f"Exception sending Slack notification: {str(e)}")

    def _get_color(self, severity: str, success: bool) -> str:
        """Get color for Slack attachment"""
        if not success:
            return "danger"  # red

        if severity == "critical":
            return "warning"  # yellow
        elif severity == "warning":
            return "#ff9900"  # orange
        else:
            return "good"  # green

    def _get_emoji(self, success: bool, dry_run: bool) -> str:
        """Get emoji for notification"""
        if dry_run:
            return ":test_tube:"
        elif success:
            return ":rocket:"
        else:
            return ":rotating_light:"
