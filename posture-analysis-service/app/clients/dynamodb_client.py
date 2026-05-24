"""Async DynamoDB client for posture event logging."""
import logging
from typing import Dict, List
import aioboto3
from botocore.exceptions import ClientError

from app.config import settings
from app.schemas.events import PostureEvent

logger = logging.getLogger(__name__)


class AsyncDynamoDBClient:
    """Async DynamoDB client for logging posture analysis events."""

    def __init__(self):
        """Initialize DynamoDB client."""
        self.table_name = settings.dynamodb_posture_events_table
        self.session = aioboto3.Session()
        self._event_buffer: List[PostureEvent] = []
        self._buffer_size = 10  # Batch write after 10 events

        logger.info(f"AsyncDynamoDBClient initialized with table: {self.table_name}")

    async def log_posture_event(
        self,
        user_id: str,
        session_id: str,
        timestamp: float,
        exercise: str,
        score: float,
        issues: List[Dict],
        rep_count: int,
        frame_number: int = 0,
    ) -> bool:
        """
        Log a posture analysis event to DynamoDB.

        Args:
            user_id: User identifier
            session_id: Session identifier
            timestamp: Event timestamp
            exercise: Exercise type
            score: Form score (0-10)
            issues: List of detected issues
            rep_count: Current rep count
            frame_number: Frame sequence number

        Returns:
            True if logged successfully
        """
        try:
            event = PostureEvent(
                user_id=user_id,
                session_id=session_id,
                timestamp=timestamp,
                exercise=exercise,
                score=score,
                issues=issues,
                rep_count=rep_count,
                frame_number=frame_number,
            )

            # Add to buffer
            self._event_buffer.append(event)

            # Batch write if buffer is full
            if len(self._event_buffer) >= self._buffer_size:
                await self._flush_buffer()

            return True

        except Exception as e:
            logger.error(f"Error logging posture event: {e}")
            return False

    async def _flush_buffer(self):
        """Flush buffered events to DynamoDB in batch."""
        if not self._event_buffer:
            return

        try:
            async with self.session.resource(
                "dynamodb",
                region_name=settings.aws_region,
                endpoint_url=settings.dynamodb_endpoint_url,
            ) as dynamodb:
                table = await dynamodb.Table(self.table_name)

                # Use batch writer for efficient writes
                async with table.batch_writer() as batch:
                    for event in self._event_buffer:
                        item = event.to_dynamodb_item()
                        await batch.put_item(Item=item)

                logger.info(f"Flushed {len(self._event_buffer)} events to DynamoDB")
                self._event_buffer.clear()

        except ClientError as e:
            logger.error(f"DynamoDB batch write error: {e}")
            # Keep events in buffer to retry later
        except Exception as e:
            logger.error(f"Error flushing event buffer: {e}")
            self._event_buffer.clear()  # Clear buffer on unknown errors

    async def get_session_events(
        self,
        user_id: str,
        session_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get all events for a session.

        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum number of events to retrieve

        Returns:
            List of event items
        """
        try:
            async with self.session.resource(
                "dynamodb",
                region_name=settings.aws_region,
                endpoint_url=settings.dynamodb_endpoint_url,
            ) as dynamodb:
                table = await dynamodb.Table(self.table_name)

                response = await table.query(
                    KeyConditionExpression="pk = :pk",
                    ExpressionAttributeValues={
                        ":pk": f"{user_id}#{session_id}"
                    },
                    Limit=limit,
                    ScanIndexForward=False  # Most recent first
                )

                return response.get("Items", [])

        except ClientError as e:
            logger.error(f"Error querying session events: {e}")
            return []

    async def close(self):
        """Close client and flush remaining events."""
        if self._event_buffer:
            logger.info("Flushing remaining events before closing")
            await self._flush_buffer()

        logger.info("AsyncDynamoDBClient closed")
