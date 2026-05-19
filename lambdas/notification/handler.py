import json
import logging
import os
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

import boto3
import requests

# Configure structured logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Environment variables
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
ENABLE_SLACK = os.getenv("ENABLE_SLACK", "false").lower() == "true"
ENABLE_EMAIL = os.getenv("ENABLE_EMAIL", "false").lower() == "true"
ENABLE_PUSH = os.getenv("ENABLE_PUSH", "false").lower() == "true"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

# AWS clients
sns_client = boto3.client("sns", region_name=AWS_REGION) if ENABLE_EMAIL or ENABLE_PUSH else None


def send_slack_notification(message: Dict[str, Any]) -> bool:
    """Send notification to Slack via webhook."""
    if not ENABLE_SLACK or not SLACK_WEBHOOK_URL:
        logger.info("Slack notifications disabled or webhook not configured")
        return False

    try:
        notification_type = message.get("type")
        user_id = message.get("userId")

        # Build Slack message
        if notification_type == "REPORT_READY":
            text = f"📊 Workout report ready for user {user_id}"
            color = "good"
        elif notification_type == "RECOMMENDATION_UPDATE":
            adjustment = message.get("adjustment", "MAINTAIN")
            text = f"💪 Workout intensity: {adjustment} for user {user_id}"
            color = "warning" if adjustment == "DECREASE" else "good"
        elif notification_type == "WORKOUT_COMPLETED":
            text = f"✅ Workout completed by user {user_id}"
            color = "good"
        else:
            text = f"🔔 Notification for user {user_id}"
            color = "#36a64f"

        payload = {
            "attachments": [
                {
                    "color": color,
                    "text": text,
                    "fields": [
                        {"title": "Type", "value": notification_type, "short": True},
                        {"title": "User", "value": user_id, "short": True},
                    ],
                }
            ]
        }

        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info(f"Slack notification sent: {notification_type}")
            return True
        else:
            logger.error(f"Slack API error: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Slack notification error: {e}")
        return False


def send_email_notification(message: Dict[str, Any]) -> bool:
    """Send email notification via SNS."""
    if not ENABLE_EMAIL or not SNS_TOPIC_ARN:
        logger.info("Email notifications disabled or SNS topic not configured")
        return False

    try:
        notification_type = message.get("type")
        user_id = message.get("userId")

        # Build email subject and body
        if notification_type == "REPORT_READY":
            subject = "Your Workout Report is Ready"
            body = f"Your workout report is ready to view.\n\nReport URL: {message.get('reportUrl')}"
        elif notification_type == "RECOMMENDATION_UPDATE":
            adjustment = message.get("adjustment", "MAINTAIN")
            subject = "Workout Intensity Update"
            body = f"Your workout intensity recommendation has been updated to: {adjustment}"
        elif notification_type == "WORKOUT_COMPLETED":
            subject = "Workout Completed"
            body = "Great job completing your workout!"
        else:
            subject = "GymPT Notification"
            body = json.dumps(message, indent=2)

        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=body,
        )

        logger.info(f"Email notification sent: {notification_type}")
        return True

    except Exception as e:
        logger.error(f"Email notification error: {e}")
        return False


def send_push_notification(message: Dict[str, Any]) -> bool:
    """
    Send push notification via SNS (Mobile Push).

    In production, this would:
    1. Look up user's device tokens from DynamoDB
    2. Send to SNS Platform Application endpoint
    3. Handle platform-specific payloads (FCM/APNS)
    """
    if not ENABLE_PUSH:
        logger.info("Push notifications disabled")
        return False

    try:
        notification_type = message.get("type")
        user_id = message.get("userId")

        # Mock push notification
        logger.info(f"[MOCK] Push notification sent to user {user_id}: {notification_type}")

        # TODO: Implement actual push via SNS Mobile Push
        # 1. Query device tokens from DynamoDB
        # 2. Format platform-specific payload
        # 3. Publish to SNS endpoint

        return True

    except Exception as e:
        logger.error(f"Push notification error: {e}")
        return False


def log_notification(message: Dict[str, Any]):
    """Log notification (local development fallback)."""
    notification_type = message.get("type", "UNKNOWN")
    user_id = message.get("userId", "unknown")

    logger.info("=" * 60)
    logger.info(f"NOTIFICATION: {notification_type}")
    logger.info(f"User: {user_id}")
    logger.info(f"Payload: {json.dumps(message, indent=2)}")
    logger.info("=" * 60)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process notification requests from SQS.

    Supported notification types:
    - REPORT_READY
    - RECOMMENDATION_UPDATE
    - WORKOUT_COMPLETED
    - POSTURE_ALERT
    - GOAL_ACHIEVED

    Message format:
    {
        "type": "REPORT_READY",
        "userId": "user-uuid",
        "reportUrl": "s3://...",
        "timestamp": "ISO timestamp"
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        processed_count = 0
        failed_count = 0

        # Process each SQS record
        for record in event.get("Records", []):
            try:
                message = json.loads(record["body"])

                notification_type = message.get("type")
                user_id = message.get("userId")

                logger.info(f"Processing notification: {notification_type} for user: {user_id}")

                # Always log notification
                log_notification(message)

                # Send to enabled channels
                results = {
                    "slack": send_slack_notification(message),
                    "email": send_email_notification(message),
                    "push": send_push_notification(message),
                }

                # Consider success if at least one channel succeeded or all disabled
                if any(results.values()) or not any([ENABLE_SLACK, ENABLE_EMAIL, ENABLE_PUSH]):
                    processed_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error processing record: {e}", exc_info=True)
                failed_count += 1

        logger.info(f"Processed {processed_count} notifications, {failed_count} failed")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "processed": processed_count,
                "failed": failed_count,
            }),
        }

    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
