from fastapi import APIRouter, HTTPException, Header
import logging
import time
from typing import Optional
from app.schemas import ReportGenerationRequest, ReportGenerationResponse
from app.services.agent_service import agent_service
from app.metrics import (
    agent_interactions_total,
    agent_interaction_duration_seconds,
    sqs_messages_published_total,
    active_requests
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/report/generate", response_model=ReportGenerationResponse)
async def generate_report(
    request: ReportGenerationRequest,
    x_internal_token: Optional[str] = Header(None)
):
    """
    Generate AI-powered workout report summary.

    Fetches user data from backend, generates summary with Bedrock,
    publishes full report task to SQS, logs to DynamoDB, and tracks metrics.
    """
    start_time = time.time()
    active_requests.inc()

    try:
        # Convert request to dict for service layer
        report_request = {
            "period_start": request.period_start,
            "period_end": request.period_end,
            "include_sections": request.include_sections
        }

        # Call agent service
        result = await agent_service.generate_report(
            user_id=request.user_id,
            report_request=report_request,
            internal_token=x_internal_token
        )

        # Track metrics
        duration = time.time() - start_time
        agent_interaction_duration_seconds.labels(
            interaction_type="report_generation"
        ).observe(duration)

        agent_interactions_total.labels(
            interaction_type="report_generation",
            status="success"
        ).inc()

        sqs_messages_published_total.labels(
            queue_name="report-generation-queue",
            task_type="report_generation"
        ).inc()

        logger.info(
            f"Report generation completed: user={request.user_id}, "
            f"task_id={result.get('task_id')}, duration={duration:.2f}s"
        )

        return ReportGenerationResponse(**result)

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        agent_interactions_total.labels(
            interaction_type="report_generation",
            status="error"
        ).inc()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate report"
        )

    finally:
        active_requests.dec()
