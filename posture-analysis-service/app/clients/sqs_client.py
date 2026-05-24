"""Async SQS client for publishing posture analysis events."""
import logging
import json
from typing import Dict, Any
from datetime import datetime
import aioboto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class AsyncSQSClient:
    """Async SQS client for publishing posture analysis completion events."""

    def __init__(self):
        """Initialize SQS client."""
        self.queue_url = settings.sqs_posture_event_queue_url
        self.session = aioboto3.Session()

        logger.info(f"AsyncSQSClient initialized with queue: {self.queue_url}")

    async def publish_posture_completed(
        self,
        user_id: str,
        session_id: str,
        summary_data: Dict[str, Any]
    ) -> bool:
        """
        Publish session completion event to SQS.

        Args:
            user_id: User identifier
            session_id: Session identifier
            summary_data: Session summary data

        Returns:
            True if published successfully
        """
        try:
            message_body = {
                "event_type": "posture_session_completed",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": summary_data,
            }

            async with self.session.client(
                "sqs",
                region_name=settings.aws_region,
                endpoint_url=settings.sqs_endpoint_url,
            ) as sqs:
                response = await sqs.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=json.dumps(message_body),
                    MessageAttributes={
                        "event_type": {
                            "StringValue": "posture_session_completed",
                            "DataType": "String",
                        },
                        "user_id": {
                            "StringValue": user_id,
                            "DataType": "String",
                        },
                    },
                )

            message_id = response.get("MessageId")
            logger.info(
                f"Published session completion to SQS: {session_id} "
                f"(MessageId: {message_id})"
            )
            return True

        except ClientError as e:
            logger.error(f"SQS publish error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing to SQS: {e}")
            return False

    async def publish_posture_issue(
        self,
        user_id: str,
        session_id: str,
        issue_data: Dict[str, Any]
    ) -> bool:
        """
        Publish high-severity issue event to SQS.

        Args:
            user_id: User identifier
            session_id: Session identifier
            issue_data: Issue details

        Returns:
            True if published successfully
        """
        try:
            message_body = {
                "event_type": "posture_issue_detected",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "issue": issue_data,
            }

            async with self.session.client(
                "sqs",
                region_name=settings.aws_region,
                endpoint_url=settings.sqs_endpoint_url,
            ) as sqs:
                await sqs.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=json.dumps(message_body),
                    MessageAttributes={
                        "event_type": {
                            "StringValue": "posture_issue_detected",
                            "DataType": "String",
                        },
                        "severity": {
                            "StringValue": issue_data.get("severity", "unknown"),
                            "DataType": "String",
                        },
                    },
                )

            logger.debug(f"Published issue event for session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error publishing issue to SQS: {e}")
            return False

    async def publish_rep_milestone(
        self,
        user_id: str,
        session_id: str,
        rep_count: int,
        exercise: str
    ) -> bool:
        """
        Publish rep milestone event (e.g., every 5 reps).

        Args:
            user_id: User identifier
            session_id: Session identifier
            rep_count: Current rep count
            exercise: Exercise type

        Returns:
            True if published successfully
        """
        try:
            message_body = {
                "event_type": "rep_milestone",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "rep_count": rep_count,
                "exercise": exercise,
            }

            async with self.session.client(
                "sqs",
                region_name=settings.aws_region,
                endpoint_url=settings.sqs_endpoint_url,
            ) as sqs:
                await sqs.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=json.dumps(message_body),
                    MessageAttributes={
                        "event_type": {
                            "StringValue": "rep_milestone",
                            "DataType": "String",
                        },
                    },
                )

            logger.info(f"Published rep milestone: {rep_count} reps for {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error publishing rep milestone: {e}")
            return False
