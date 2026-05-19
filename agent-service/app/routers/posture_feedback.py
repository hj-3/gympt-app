from fastapi import APIRouter, HTTPException
import logging
import time
from app.schemas import PostureFeedbackRequest, PostureFeedbackResponse
from app.services.agent_service import agent_service
from app.metrics import (
    agent_interactions_total,
    agent_interaction_duration_seconds,
    active_requests
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/posture/feedback", response_model=PostureFeedbackResponse)
async def provide_posture_feedback(request: PostureFeedbackRequest):
    """
    Provide real-time posture correction feedback.

    Analyzes exercise form, provides corrections, logs to DynamoDB,
    and tracks metrics.
    """
    start_time = time.time()
    active_requests.inc()

    try:
        # Extract user_id from session_id (format: user_id-timestamp)
        user_id = request.session_id.split("-")[0] if "-" in request.session_id else "unknown"

        # Convert request to dict for service layer
        posture_request = {
            "session_id": request.session_id,
            "exercise_name": request.exercise_name,
            "posture_score": request.posture_score,
            "detected_issues": request.detected_issues,
            "frame_data": request.frame_data
        }

        # Call agent service
        result = await agent_service.generate_posture_feedback(
            user_id=user_id,
            posture_request=posture_request
        )

        # Track metrics
        duration = time.time() - start_time
        agent_interaction_duration_seconds.labels(
            interaction_type="posture_feedback"
        ).observe(duration)

        agent_interactions_total.labels(
            interaction_type="posture_feedback",
            status="success"
        ).inc()

        logger.info(
            f"Posture feedback completed: session={request.session_id}, "
            f"severity={result.get('severity')}, duration={duration:.2f}s"
        )

        return PostureFeedbackResponse(**result)

    except Exception as e:
        logger.error(f"Posture feedback failed: {e}")
        agent_interactions_total.labels(
            interaction_type="posture_feedback",
            status="error"
        ).inc()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate posture feedback"
        )

    finally:
        active_requests.dec()
