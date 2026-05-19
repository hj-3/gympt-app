from fastapi import APIRouter, HTTPException, Header
import logging
import time
from typing import Optional
from app.schemas import WorkoutRecommendationRequest, WorkoutRecommendationResponse
from app.services.agent_service import agent_service
from app.metrics import (
    agent_interactions_total,
    agent_interaction_duration_seconds,
    cache_hits_total,
    cache_misses_total,
    active_requests
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/workout/recommend", response_model=WorkoutRecommendationResponse)
async def recommend_workout(
    request: WorkoutRecommendationRequest,
    x_internal_token: Optional[str] = Header(None)
):
    """
    Generate personalized workout recommendation using AI.

    Fetches user profile from backend, uses cache for repeated requests,
    logs interaction to DynamoDB, and tracks metrics.
    """
    start_time = time.time()
    active_requests.inc()

    try:
        # Convert request to dict for service layer
        workout_request = {
            "goal": request.goal.value,
            "fitness_level": request.fitness_level.value,
            "days_per_week": request.days_per_week,
            "equipment_available": request.equipment_available,
            "injuries_or_limitations": request.injuries_or_limitations
        }

        # Call agent service
        result = await agent_service.generate_workout_plan(
            user_id=request.user_id,
            workout_request=workout_request,
            internal_token=x_internal_token,
            use_cache=True
        )

        # Track metrics
        duration = time.time() - start_time
        agent_interaction_duration_seconds.labels(
            interaction_type="workout_recommend"
        ).observe(duration)

        agent_interactions_total.labels(
            interaction_type="workout_recommend",
            status="success"
        ).inc()

        if result.get("cached"):
            cache_hits_total.labels(endpoint="workout_recommend").inc()
        else:
            cache_misses_total.labels(endpoint="workout_recommend").inc()

        logger.info(
            f"Workout recommendation completed: user={request.user_id}, "
            f"cached={result.get('cached')}, duration={duration:.2f}s"
        )

        return WorkoutRecommendationResponse(**result)

    except Exception as e:
        logger.error(f"Workout recommendation failed: {e}")
        agent_interactions_total.labels(
            interaction_type="workout_recommend",
            status="error"
        ).inc()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate workout recommendation"
        )

    finally:
        active_requests.dec()
