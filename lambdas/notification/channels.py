"""Notification channel handlers."""

import logging
import time
from typing import Any, Dict, Optional

import boto3
import httpx

from templates import NotificationTemplate

logger = logging.getLogger(__name__)


class BaseChannel:
    """Base class for notification channels."""

    def __init__(self):
        """Initialize channel."""
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def send(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """Send notification with retry logic."""
        for attempt in range(self.max_retries):
            try:
                result = self._send_impl(notification_type, data)
                if result:
                    logger.info(
                        f"Successfully sent {notification_type} via {self.__class__.__name__}"
                    )
                    return True
                else:
                    logger.warning(
                        f"Failed to send {notification_type} via {self.__class__.__name__}, "
                        f"attempt {attempt + 1}/{self.max_retries}"
                    )
            except Exception as e:
                logger.error(
                    f"Error sending {notification_type} via {self.__class__.__name__}: {e}",
                    exc_info=True,
                )

            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = self.retry_delay * (2**attempt)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

        logger.error(f"Failed to send {notification_type} after {self.max_retries} attempts")
        return False

    def _send_impl(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """Implementation-specific send logic. Override in subclasses."""
        raise NotImplementedError


class SlackChannel(BaseChannel):
    """Slack webhook notification channel."""

    def __init__(self, webhook_url: str):
        """Initialize Slack channel."""
        super().__init__()
        self.webhook_url = webhook_url

    def _send_impl(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """Send notification to Slack."""
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        # Render Slack message
        payload = NotificationTemplate.render_slack(notification_type, data)

        # Send to Slack
        with httpx.Client(timeout=10.0) as client:
            response = client.post(self.webhook_url, json=payload)

            if response.status_code == 200:
                return True
            else:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return False


class EmailChannel(BaseChannel):
    """Email notification channel via SNS."""

    def __init__(self, sns_topic_arn: str, region: str = "ap-northeast-2"):
        """Initialize email channel."""
        super().__init__()
        self.sns_topic_arn = sns_topic_arn
        self.sns_client = boto3.client("sns", region_name=region)

    def _send_impl(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """Send notification via email."""
        if not self.sns_topic_arn:
            logger.warning("SNS topic ARN not configured")
            return False

        # Render email
        email = NotificationTemplate.render_email(notification_type, data)

        # Publish to SNS
        try:
            self.sns_client.publish(
                TopicArn=self.sns_topic_arn,
                Subject=email["subject"],
                Message=email["body"],
            )
            return True
        except Exception as e:
            logger.error(f"SNS publish error: {e}")
            return False


class PushChannel(BaseChannel):
    """Push notification channel via SNS Mobile Push."""

    def __init__(self, region: str = "ap-northeast-2"):
        """Initialize push channel."""
        super().__init__()
        self.sns_client = boto3.client("sns", region_name=region)
        self.dynamodb = boto3.resource("dynamodb", region_name=region)

    def _get_device_endpoints(self, user_id: str) -> list:
        """
        Get SNS endpoint ARNs for user's devices.

        In production:
        1. Query DynamoDB table for user's registered devices
        2. Return list of SNS Platform Application endpoint ARNs
        """
        # TODO: Implement device endpoint lookup
        # table = self.dynamodb.Table("gympt-user-devices")
        # response = table.query(KeyConditionExpression="userId = :uid", ...)
        # return [item["endpointArn"] for item in response["Items"]]

        logger.warning(f"Device endpoint lookup not implemented for user: {user_id}")
        return []

    def _send_impl(self, notification_type: str, data: Dict[str, Any]) -> bool:
        """Send push notification."""
        user_id = data.get("userId")
        if not user_id:
            logger.error("User ID required for push notifications")
            return False

        # Get device endpoints
        endpoints = self._get_device_endpoints(user_id)
        if not endpoints:
            logger.info(f"No push endpoints found for user: {user_id}")
            # Return True since this is not an error - user may not have push enabled
            return True

        # Render push notification
        push = NotificationTemplate.render_push(notification_type, data)

        # Format platform-specific payloads
        # FCM (Android)
        fcm_payload = {
            "notification": {
                "title": push["title"],
                "body": push["body"],
            },
            "data": push["data"],
        }

        # APNs (iOS)
        apns_payload = {
            "aps": {
                "alert": {
                    "title": push["title"],
                    "body": push["body"],
                },
                "sound": "default",
            },
            "data": push["data"],
        }

        # Send to each endpoint
        success_count = 0
        for endpoint_arn in endpoints:
            try:
                # Determine platform from endpoint ARN
                if "GCM" in endpoint_arn:
                    message = {"GCM": str(fcm_payload)}
                elif "APNS" in endpoint_arn:
                    message = {"APNS": str(apns_payload)}
                else:
                    # Default/fallback
                    message = {"default": push["body"]}

                self.sns_client.publish(
                    TargetArn=endpoint_arn,
                    Message=str(message),
                    MessageStructure="json",
                )
                success_count += 1

            except Exception as e:
                logger.error(f"Error sending to endpoint {endpoint_arn}: {e}")

        return success_count > 0


class NotificationChannelManager:
    """Manages multiple notification channels."""

    def __init__(
        self,
        slack_webhook_url: Optional[str] = None,
        sns_email_topic: Optional[str] = None,
        enable_push: bool = False,
        region: str = "ap-northeast-2",
    ):
        """Initialize channel manager."""
        self.channels = {}

        if slack_webhook_url:
            self.channels["slack"] = SlackChannel(slack_webhook_url)

        if sns_email_topic:
            self.channels["email"] = EmailChannel(sns_email_topic, region)

        if enable_push:
            self.channels["push"] = PushChannel(region)

    def send(
        self, notification_type: str, data: Dict[str, Any], channels: Optional[list] = None
    ) -> Dict[str, bool]:
        """
        Send notification to specified channels.

        Args:
            notification_type: Type of notification
            data: Notification data
            channels: List of channel names to use (default: all enabled)

        Returns:
            Dict mapping channel name to success status
        """
        if channels is None:
            channels = list(self.channels.keys())

        results = {}
        for channel_name in channels:
            channel = self.channels.get(channel_name)
            if channel:
                results[channel_name] = channel.send(notification_type, data)
            else:
                logger.warning(f"Channel not configured: {channel_name}")
                results[channel_name] = False

        return results

    def send_to_all(self, notification_type: str, data: Dict[str, Any]) -> Dict[str, bool]:
        """Send notification to all enabled channels."""
        return self.send(notification_type, data)
