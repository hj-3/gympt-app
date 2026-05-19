"""Enhanced frame processor with MediaPipe, rep counting, and AWS integration."""
import asyncio
import time
import logging
from typing import Dict, Any, Optional
import numpy as np

from app.config import settings
from app.pose_estimator.base import PoseEstimator
from app.pose_estimator.mock_estimator import MockPoseEstimator
from app.pose_estimator.mediapipe_estimator import MediaPipePoseEstimator
from app.counting.rep_counter import RepCounter
from app.rules.squat_rule import SquatRule
from app.rules.pushup_rule import PushupRule
from app.rules.plank_rule import PlankRule
from app.rules.deadlift_rule import DeadliftRule
from app.services.session_service import SessionService
from app.clients.dynamodb_client import AsyncDynamoDBClient
from app.schemas.websocket import WebSocketResponse
from app.schemas.analysis import IssueDetail, Severity
from app.metrics import (
    frames_processed_total,
    frame_processing_duration,
    pose_estimation_errors_total,
    rep_count_total,
    posture_score_distribution,
)

logger = logging.getLogger(__name__)


class EnhancedFrameProcessor:
    """Enhanced frame processor with full feature set."""

    def __init__(self):
        """Initialize enhanced frame processor."""
        # Initialize pose estimator based on model type
        self.estimator = self._create_estimator()

        # Initialize exercise rules
        self.rules = {
            "squat": SquatRule(self.estimator),
            "pushup": PushupRule(self.estimator),
            "plank": PlankRule(self.estimator),
            "deadlift": DeadliftRule(self.estimator),
        }

        # Initialize AWS clients
        self.dynamodb = AsyncDynamoDBClient()
        self.session_service = SessionService(dynamodb_client=self.dynamodb)

        # Rep counters per session
        self.rep_counters: Dict[str, RepCounter] = {}

        # Frame counters per session
        self.frame_counts: Dict[str, int] = {}

        # Last DynamoDB log timestamp per session
        self.last_log_time: Dict[str, float] = {}

        logger.info(
            f"EnhancedFrameProcessor initialized with model: {settings.model_type}"
        )

    def _create_estimator(self) -> PoseEstimator:
        """Create pose estimator based on configuration."""
        if settings.model_type == "mediapipe":
            try:
                return MediaPipePoseEstimator(enable_gpu=settings.enable_gpu)
            except RuntimeError as e:
                logger.warning(f"Failed to initialize MediaPipe: {e}. Falling back to mock.")
                return MockPoseEstimator()
        else:
            logger.info("Using mock pose estimator")
            return MockPoseEstimator()

    async def start_session(
        self,
        user_id: str,
        exercise_type: str
    ) -> str:
        """
        Start a new analysis session.

        Args:
            user_id: User identifier
            exercise_type: Exercise type

        Returns:
            session_id
        """
        session_id = await self.session_service.start_session(user_id, exercise_type)

        # Initialize rep counter for this session
        thresholds = settings.rep_counter_thresholds.get(exercise_type)
        self.rep_counters[session_id] = RepCounter(
            exercise_type=exercise_type,
            thresholds=thresholds
        )

        # Initialize counters
        self.frame_counts[session_id] = 0
        self.last_log_time[session_id] = time.time()

        logger.info(f"Session started: {session_id} for exercise: {exercise_type}")
        return session_id

    async def process_frame(
        self,
        frame: np.ndarray,
        session_id: str,
        exercise_type: str
    ) -> WebSocketResponse:
        """
        Process a single frame with full feature set.

        Args:
            frame: Video frame
            session_id: Session identifier
            exercise_type: Exercise type

        Returns:
            WebSocketResponse with analysis results
        """
        start_time = time.time()

        try:
            self.frame_counts[session_id] = self.frame_counts.get(session_id, 0) + 1
            frame_number = self.frame_counts[session_id]

            # 1. Pose Estimation
            pose_data = await self.estimator.estimate(frame)

            if pose_data.get("confidence", 0) < 0.5:
                logger.warning(f"Low confidence pose detection: {pose_data.get('confidence')}")
                pose_estimation_errors_total.labels(
                    model_type=settings.model_type,
                    error_type="low_confidence"
                ).inc()

            # 2. Form Analysis
            rule = self.rules.get(exercise_type)
            if not rule:
                logger.error(f"No rule found for exercise: {exercise_type}")
                return WebSocketResponse(
                    status="error",
                    error=f"Unsupported exercise type: {exercise_type}"
                )

            analysis_result = await rule.analyze(pose_data)

            # 3. Rep Counting
            rep_counter = self.rep_counters.get(session_id)
            if rep_counter:
                rep_result = rep_counter.count_reps(pose_data.get("keypoints", {}))
                rep_count = rep_result.total_reps
                current_state = rep_result.current_state

                # Track rep count metric
                if rep_count > rep_counter.total_reps:
                    rep_count_total.labels(
                        exercise_type=exercise_type,
                        user_id=session_id.split("_")[0]  # Extract user_id
                    ).inc()
            else:
                rep_count = 0
                current_state = "starting"

            # 4. Update Session Metrics
            score = analysis_result.get("score", 0.0)
            issues = analysis_result.get("issues", [])

            await self.session_service.update_session_metrics(
                session_id=session_id,
                rep_count=rep_count,
                score=score,
                issues=issues
            )

            # 5. Log to DynamoDB (every N seconds or on issue detection)
            current_time = time.time()
            last_log = self.last_log_time.get(session_id, 0)
            should_log = (
                current_time - last_log >= settings.log_interval_seconds
                or len(issues) > 0
            )

            if should_log:
                await self._log_to_dynamodb(
                    session_id=session_id,
                    timestamp=current_time,
                    exercise=exercise_type,
                    score=score,
                    issues=issues,
                    rep_count=rep_count,
                    frame_number=frame_number
                )
                self.last_log_time[session_id] = current_time

            # 6. Get Session Summary
            session_metrics = await self.session_service.get_session_metrics(session_id)

            # 7. Build Response
            response = WebSocketResponse(
                status="success",
                session_id=session_id,
                exercise=exercise_type,
                score=score,
                rep_count=rep_count,
                total_reps=rep_count,
                avg_score=session_metrics.current_score if session_metrics else score,
                issues=[
                    IssueDetail(**issue) for issue in issues
                ],
                feedback=self._generate_feedback(score, issues),
                timestamp=current_time,
                frame_number=frame_number,
            )

            # 8. Record Metrics
            processing_time = time.time() - start_time
            frames_processed_total.labels(
                exercise_type=exercise_type,
                model_type=settings.model_type
            ).inc()

            frame_processing_duration.labels(
                exercise_type=exercise_type
            ).observe(processing_time)

            posture_score_distribution.labels(
                exercise_type=exercise_type
            ).observe(score)

            return response

        except Exception as e:
            logger.error(f"Error processing frame: {e}", exc_info=True)
            pose_estimation_errors_total.labels(
                model_type=settings.model_type,
                error_type="processing_error"
            ).inc()

            return WebSocketResponse(
                status="error",
                session_id=session_id,
                error=str(e)
            )

    async def end_session(self, session_id: str):
        """
        End a session and generate summary.

        Args:
            session_id: Session identifier
        """
        try:
            summary = await self.session_service.end_session(session_id)

            # Cleanup
            self.rep_counters.pop(session_id, None)
            self.frame_counts.pop(session_id, None)
            self.last_log_time.pop(session_id, None)

            logger.info(f"Session ended: {session_id}")
            return summary

        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return None

    async def _log_to_dynamodb(
        self,
        session_id: str,
        timestamp: float,
        exercise: str,
        score: float,
        issues: list,
        rep_count: int,
        frame_number: int
    ):
        """Log event to DynamoDB."""
        try:
            user_id = session_id.split("_")[0]  # Extract user_id from session_id

            await self.dynamodb.log_posture_event(
                user_id=user_id,
                session_id=session_id,
                timestamp=timestamp,
                exercise=exercise,
                score=score,
                issues=issues,
                rep_count=rep_count,
                frame_number=frame_number
            )

        except Exception as e:
            logger.error(f"Error logging to DynamoDB: {e}")

    def _generate_feedback(self, score: float, issues: list) -> str:
        """
        Generate real-time feedback message.

        Args:
            score: Form score
            issues: List of issues

        Returns:
            Feedback message
        """
        if score >= 9.0:
            return "Excellent form! Keep it up!"
        elif score >= 8.0:
            return "Great form! Minor improvements possible."
        elif score >= 7.0:
            if issues:
                issue_types = [issue.get("type", "issue") for issue in issues]
                return f"Good form. Watch: {', '.join(issue_types[:2])}"
            return "Good form overall. Stay focused."
        elif score >= 5.0:
            if issues:
                primary_issue = issues[0]
                return f"Form needs work: {primary_issue.get('correction', 'Check your technique')}"
            return "Form needs improvement. Focus on technique."
        else:
            return "Poor form detected. Stop and review technique."

    async def cleanup(self):
        """Cleanup resources."""
        await self.dynamodb.close()
        logger.info("EnhancedFrameProcessor cleaned up")
