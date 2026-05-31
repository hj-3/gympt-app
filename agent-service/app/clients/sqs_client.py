import aioboto3
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class AsyncSQSClient:
    """Async SQS client for publishing agent tasks."""

    def __init__(self):
        self.session = aioboto3.Session()
        self.region = settings.aws_region
        self.endpoint_url = settings.sqs_endpoint_url

    async def publish_task(
        self,
        queue_name: str,
        message_body: Dict[str, Any],
        message_attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Publish a task message to SQS queue.

        Args:
            queue_name: Queue name (posture-analysis-queue, report-generation-queue)
            message_body: Message payload as dict
            message_attributes: Optional message attributes

        Returns:
            Message ID if successful, None otherwise
        """
        try:
            # Get queue URL from config
            queue_url = self._get_queue_url(queue_name)
            if not queue_url:
                logger.error(f"Queue URL not configured for: {queue_name}")
                return None

            async with self.session.client(
                "sqs",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            ) as sqs:
                # Prepare message
                params = {
                    "QueueUrl": queue_url,
                    "MessageBody": json.dumps(message_body)
                }

                # Add message attributes if provided
                if message_attributes:
                    formatted_attrs = {}
                    for key, value in message_attributes.items():
                        if isinstance(value, str):
                            formatted_attrs[key] = {
                                "StringValue": value,
                                "DataType": "String"
                            }
                        elif isinstance(value, int):
                            formatted_attrs[key] = {
                                "StringValue": str(value),
                                "DataType": "Number"
                            }
                    params["MessageAttributes"] = formatted_attrs

                # Send message
                response = await sqs.send_message(**params)
                message_id = response.get("MessageId")

                logger.info(
                    f"Published message to SQS: queue={queue_name}, "
                    f"message_id={message_id}"
                )
                return message_id

        except Exception as e:
            logger.error(f"Failed to publish message to SQS: {e}")
            # Don't raise - graceful degradation
            return None

    async def publish_posture_analysis_task(
        self,
        session_id: str,
        user_id: str,
        exercise_name: str,
        frame_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Publish a posture analysis task.

        Args:
            session_id: Workout session ID
            user_id: User identifier
            exercise_name: Exercise name
            frame_data: Pose landmark data

        Returns:
            Message ID if successful
        """
        message_body = {
            "task_type": "posture_analysis",
            "session_id": session_id,
            "user_id": user_id,
            "exercise_name": exercise_name,
            "frame_data": frame_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        message_attributes = {
            "TaskType": "posture_analysis",
            "Priority": "high"
        }

        return await self.publish_task(
            "posture-analysis-queue",
            message_body,
            message_attributes
        )

    async def publish_report_generation_task(
        self,
        user_id: str,
        report_id: str,
        period_start: str,
        period_end: str,
        report_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Publish a report generation task.

        Args:
            user_id: User identifier
            report_id: Report task ID
            period_start: Report period start
            period_end: Report period end
            report_data: Full report data

        Returns:
            Message ID if successful
        """
        message_body = {
            "task_type": "report_generation",
            "user_id": user_id,
            "report_id": report_id,
            "period_start": period_start,
            "period_end": period_end,
            "report_data": report_data,
            "environment": settings.app_env
        }

        message_attributes = {
            "TaskType": "report_generation",
            "Priority": "normal"
        }

        return await self.publish_task(
            "report-generation-queue",
            message_body,
            message_attributes
        )

    def _get_queue_url(self, queue_name: str) -> Optional[str]:
        """
        Get queue URL from configuration.

        Args:
            queue_name: Queue name

        Returns:
            Queue URL or None
        """
        # For LocalStack/local development
        if settings.is_local and self.endpoint_url:
            return f"{self.endpoint_url}/000000000000/{queue_name}"

        # For dev/prod environments
        queue_urls = {
            "posture-analysis-queue": f"https://sqs.{self.region}.amazonaws.com/ACCOUNT_ID/gympt-posture-analysis-{settings.app_env}",
            "report-generation-queue": f"https://sqs.{self.region}.amazonaws.com/ACCOUNT_ID/gympt-report-generation-{settings.app_env}"
        }

        # If explicit queue URL is configured, use it
        if settings.sqs_agent_task_queue_url:
            return settings.sqs_agent_task_queue_url

        return queue_urls.get(queue_name)


# Singleton instance
sqs_client = AsyncSQSClient()
