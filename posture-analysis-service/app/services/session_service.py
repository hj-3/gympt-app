"""Session management service for posture analysis."""
import logging
import json
from typing import Dict, Optional, List
from datetime import datetime

from app.schemas.session import SessionSummary, SessionState, SessionMetrics
from app.clients.redis_client import redis_client
from app.clients.dynamodb_client import AsyncDynamoDBClient
from app.clients.s3_client import AsyncS3Client
from app.clients.sqs_client import AsyncSQSClient

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing posture analysis sessions."""

    def __init__(
        self,
        dynamodb_client: Optional[AsyncDynamoDBClient] = None,
        s3_client: Optional[AsyncS3Client] = None,
        sqs_client: Optional[AsyncSQSClient] = None,
    ):
        """
        Initialize session service.

        Args:
            dynamodb_client: DynamoDB client for event logging
            s3_client: S3 client for result storage
            sqs_client: SQS client for event publishing
        """
        self.dynamodb = dynamodb_client or AsyncDynamoDBClient()
        self.s3 = s3_client or AsyncS3Client()
        self.sqs = sqs_client or AsyncSQSClient()
        self.redis = redis_client

        logger.info("SessionService initialized")

    async def start_session(
        self,
        user_id: str,
        exercise_type: str
    ) -> str:
        """
        Start a new analysis session.

        Args:
            user_id: User identifier
            exercise_type: Type of exercise

        Returns:
            Generated session_id
        """
        try:
            # Generate session ID
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            session_id = f"{user_id}_{timestamp}"

            # Initialize session state in Redis
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "exercise_type": exercise_type,
                "state": SessionState.ACTIVE.value,
                "started_at": datetime.utcnow().isoformat(),
                "total_reps": 0,
                "total_score": 0.0,
                "frames_processed": 0,
                "issues_detected": 0,
                "issues_summary": {},
            }

            # Store in Redis with 24h expiration
            session_key = f"session:{session_id}"
            await self.redis.setex(
                session_key,
                86400,  # 24 hours
                json.dumps(session_data)
            )

            logger.info(f"Started session: {session_id} for user: {user_id}")
            return session_id

        except Exception as e:
            logger.error(f"Error starting session: {e}")
            raise

    async def update_session_metrics(
        self,
        session_id: str,
        rep_count: int,
        score: float,
        issues: List[Dict],
    ):
        """
        Update session metrics after processing a frame.

        Args:
            session_id: Session identifier
            rep_count: Current rep count
            score: Current form score
            issues: Detected issues
        """
        try:
            session_key = f"session:{session_id}"
            session_data_str = await self.redis.get(session_key)

            if not session_data_str:
                logger.warning(f"Session not found: {session_id}")
                return

            session_data = json.loads(session_data_str)

            # Update metrics
            session_data["total_reps"] = rep_count
            session_data["frames_processed"] += 1

            # Update running average score
            frames = session_data["frames_processed"]
            current_avg = session_data.get("total_score", 0.0)
            session_data["total_score"] = (current_avg * (frames - 1) + score) / frames

            # Update issues summary
            issues_summary = session_data.get("issues_summary", {})
            for issue in issues:
                issue_type = issue.get("type", "unknown")
                issues_summary[issue_type] = issues_summary.get(issue_type, 0) + 1

            session_data["issues_summary"] = issues_summary
            session_data["issues_detected"] = sum(issues_summary.values())

            # Update last rep timestamp
            if rep_count > session_data.get("last_rep_count", 0):
                session_data["last_rep_at"] = datetime.utcnow().isoformat()
                session_data["last_rep_count"] = rep_count

            # Save back to Redis
            await self.redis.setex(
                session_key,
                86400,
                json.dumps(session_data)
            )

        except Exception as e:
            logger.error(f"Error updating session metrics: {e}")

    async def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """
        Get current session metrics.

        Args:
            session_id: Session identifier

        Returns:
            SessionMetrics or None if not found
        """
        try:
            session_key = f"session:{session_id}"
            session_data_str = await self.redis.get(session_key)

            if not session_data_str:
                return None

            session_data = json.loads(session_data_str)

            # Calculate elapsed time
            started_at = datetime.fromisoformat(session_data["started_at"])
            elapsed_seconds = (datetime.utcnow() - started_at).total_seconds()

            return SessionMetrics(
                session_id=session_id,
                current_reps=session_data.get("total_reps", 0),
                current_score=session_data.get("total_score", 0.0),
                frames_processed=session_data.get("frames_processed", 0),
                issues_count=session_data.get("issues_detected", 0),
                elapsed_seconds=elapsed_seconds,
                last_rep_at=session_data.get("last_rep_at"),
            )

        except Exception as e:
            logger.error(f"Error getting session metrics: {e}")
            return None

    async def end_session(self, session_id: str) -> Optional[SessionSummary]:
        """
        End a session and generate summary.

        Args:
            session_id: Session identifier

        Returns:
            SessionSummary with results
        """
        try:
            # Get session data from Redis
            session_key = f"session:{session_id}"
            session_data_str = await self.redis.get(session_key)

            if not session_data_str:
                logger.warning(f"Session not found: {session_id}")
                return None

            session_data = json.loads(session_data_str)

            # Calculate duration
            started_at = datetime.fromisoformat(session_data["started_at"])
            ended_at = datetime.utcnow()
            duration_seconds = (ended_at - started_at).total_seconds()

            # Create summary
            summary = SessionSummary(
                session_id=session_id,
                user_id=session_data["user_id"],
                exercise_type=session_data["exercise_type"],
                total_reps=session_data.get("total_reps", 0),
                avg_score=session_data.get("total_score", 0.0),
                duration_seconds=duration_seconds,
                issues_detected=session_data.get("issues_detected", 0),
                issues_summary=session_data.get("issues_summary", {}),
                started_at=started_at,
                ended_at=ended_at,
                state=SessionState.COMPLETED,
                total_frames_processed=session_data.get("frames_processed", 0),
            )

            # Upload summary to S3
            s3_key = await self.s3.upload_analysis_result(
                user_id=summary.user_id,
                session_id=session_id,
                analysis_data=summary.model_dump(mode='json')
            )

            if s3_key:
                summary.s3_result_key = s3_key

            # Publish completion event to SQS
            await self.sqs.publish_posture_completed(
                user_id=summary.user_id,
                session_id=session_id,
                summary_data=summary.model_dump(mode='json')
            )

            # Update session state in Redis
            session_data["state"] = SessionState.COMPLETED.value
            session_data["ended_at"] = ended_at.isoformat()
            await self.redis.setex(
                session_key,
                86400,
                json.dumps(session_data)
            )

            # Flush any remaining DynamoDB events
            await self.dynamodb.close()

            logger.info(
                f"Session ended: {session_id}, "
                f"Reps: {summary.total_reps}, "
                f"Avg Score: {summary.avg_score:.2f}"
            )

            return summary

        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return None

    async def pause_session(self, session_id: str):
        """Pause an active session."""
        try:
            session_key = f"session:{session_id}"
            session_data_str = await self.redis.get(session_key)

            if session_data_str:
                session_data = json.loads(session_data_str)
                session_data["state"] = SessionState.PAUSED.value
                session_data["paused_at"] = datetime.utcnow().isoformat()

                await self.redis.setex(
                    session_key,
                    86400,
                    json.dumps(session_data)
                )

                logger.info(f"Session paused: {session_id}")

        except Exception as e:
            logger.error(f"Error pausing session: {e}")

    async def resume_session(self, session_id: str):
        """Resume a paused session."""
        try:
            session_key = f"session:{session_id}"
            session_data_str = await self.redis.get(session_key)

            if session_data_str:
                session_data = json.loads(session_data_str)
                session_data["state"] = SessionState.ACTIVE.value
                session_data.pop("paused_at", None)

                await self.redis.setex(
                    session_key,
                    86400,
                    json.dumps(session_data)
                )

                logger.info(f"Session resumed: {session_id}")

        except Exception as e:
            logger.error(f"Error resuming session: {e}")
