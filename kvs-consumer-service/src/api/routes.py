"""API routes for KVS Consumer Service."""
import logging
import asyncio
import base64
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx
import cv2
import numpy as np

from ..config.settings import settings
from ..services.kvs_stream_consumer import KVSStreamConsumer

logger = logging.getLogger(__name__)
router = APIRouter()

# Active consumers registry
active_consumers = {}


class StartConsumerRequest(BaseModel):
    """Request to start consuming a KVS stream."""
    channel_name: str
    session_id: str
    user_id: str
    exercise: str


class StopConsumerRequest(BaseModel):
    """Request to stop consuming a KVS stream."""
    session_id: str


@router.post("/consume/start")
async def start_consumer(
    request: StartConsumerRequest,
    background_tasks: BackgroundTasks
):
    """
    Start consuming KVS stream for a session.

    Args:
        request: Consumer start request

    Returns:
        Consumer status
    """
    if request.session_id in active_consumers:
        raise HTTPException(
            status_code=400,
            detail=f"Consumer already running for session {request.session_id}"
        )

    # Create consumer
    consumer = KVSStreamConsumer(
        channel_name=request.channel_name,
        session_id=request.session_id
    )

    # Create frame processing callback
    async def process_frame(frame: np.ndarray, frame_number: int):
        """Process captured frame."""
        try:
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            # Send to posture analysis service
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{settings.posture_analysis_url}/analyze",
                    json={
                        "exercise": request.exercise,
                        "frame_base64": frame_base64,
                        "session_id": request.session_id,
                        "user_id": request.user_id,
                        "rep_count": 0,
                        "send_websocket": True,
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Posture analysis failed: {response.text}")

        except Exception as e:
            logger.error(f"Error processing frame {frame_number}: {e}")

    # Start consumer in background
    background_tasks.add_task(
        consumer.start_consuming,
        process_frame
    )

    # Register consumer
    active_consumers[request.session_id] = consumer

    logger.info(f"Started KVS consumer for session {request.session_id}")

    return {
        "status": "started",
        "session_id": request.session_id,
        "channel_name": request.channel_name,
    }


@router.post("/consume/stop")
async def stop_consumer(request: StopConsumerRequest):
    """
    Stop consuming KVS stream for a session.

    Args:
        request: Consumer stop request

    Returns:
        Consumer status
    """
    consumer = active_consumers.get(request.session_id)

    if not consumer:
        raise HTTPException(
            status_code=404,
            detail=f"No active consumer for session {request.session_id}"
        )

    # Stop consumer
    await consumer.stop_consuming()

    # Unregister consumer
    del active_consumers[request.session_id]

    logger.info(f"Stopped KVS consumer for session {request.session_id}")

    return {
        "status": "stopped",
        "session_id": request.session_id,
    }


@router.get("/consume/status/{session_id}")
async def get_consumer_status(session_id: str):
    """
    Get consumer status for a session.

    Args:
        session_id: Session identifier

    Returns:
        Consumer status
    """
    consumer = active_consumers.get(session_id)

    if not consumer:
        return {
            "session_id": session_id,
            "status": "not_running",
        }

    return {
        "session_id": session_id,
        "status": "running",
        "channel_name": consumer.channel_name,
        "frame_count": consumer.frame_counter,
    }


@router.get("/consume/active")
async def list_active_consumers():
    """
    List all active consumers.

    Returns:
        List of active consumers
    """
    consumers = []

    for session_id, consumer in active_consumers.items():
        consumers.append({
            "session_id": session_id,
            "channel_name": consumer.channel_name,
            "frame_count": consumer.frame_counter,
        })

    return {
        "count": len(consumers),
        "consumers": consumers,
    }
