"""
API Routes for Posture Analysis Service
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Request
from pydantic import BaseModel
from typing import Optional
import cv2
import numpy as np
import base64

from ..services.websocket_client import WebSocketClient

router = APIRouter()

# Initialize WebSocket client
ws_client = WebSocketClient()


class AnalyzeFrameRequest(BaseModel):
    """Request model for frame analysis"""
    exercise: str
    frame_base64: str
    rep_phase: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    rep_count: Optional[int] = 0
    send_websocket: Optional[bool] = False


class AnalyzeFrameResponse(BaseModel):
    """Response model for frame analysis"""
    form_score: float
    is_valid: bool
    feedback: list[str]
    angles: dict
    landmarks_count: int


@router.post("/analyze", response_model=AnalyzeFrameResponse)
async def analyze_frame(request: AnalyzeFrameRequest, req: Request):
    """
    Analyze a single video frame for exercise form

    Args:
        exercise: Exercise name (squat, pushup, deadlift, plank)
        frame_base64: Base64-encoded image (JPEG/PNG)
        rep_phase: Optional rep phase (down, up, hold)
        session_id: Optional session ID for tracking

    Returns:
        Form analysis results
    """
    try:
        # Get models from app state
        models = req.app.state.models
        pose_estimator = models["pose_estimator"]
        form_analyzer = models["form_analyzer"]

        # Decode base64 image
        try:
            image_bytes = base64.b64decode(request.frame_base64)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                raise ValueError("Failed to decode image")

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")

        # Process frame with pose estimator
        pose_result = pose_estimator.process_frame(frame)

        if pose_result is None:
            return AnalyzeFrameResponse(
                form_score=0.0,
                is_valid=False,
                feedback=["No person detected in frame. Ensure full body is visible."],
                angles={},
                landmarks_count=0,
            )

        # Analyze form
        form_result = form_analyzer.analyze(
            exercise=request.exercise,
            landmarks=pose_result["landmarks"],
            rep_phase=request.rep_phase,
        )

        if "error" in form_result:
            raise HTTPException(status_code=400, detail=form_result["error"])

        response = AnalyzeFrameResponse(
            form_score=form_result["form_score"],
            is_valid=form_result["is_valid"],
            feedback=form_result["feedback"],
            angles=form_result.get("angles", {}),
            landmarks_count=len(pose_result["landmarks"]),
        )

        # Send to WebSocket if requested
        if request.send_websocket and request.session_id and request.user_id:
            await ws_client.send_feedback(
                session_id=request.session_id,
                user_id=request.user_id,
                exercise=request.exercise,
                rep_count=request.rep_count or 0,
                form_score=form_result["form_score"],
                is_valid=form_result["is_valid"],
                feedback=form_result["feedback"],
                angles=form_result.get("angles", {}),
                message_type="feedback",
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/upload")
async def analyze_uploaded_image(
    exercise: str,
    file: UploadFile = File(...),
    rep_phase: Optional[str] = None,
    request: Request = None,
):
    """
    Analyze an uploaded image file

    Args:
        exercise: Exercise name
        file: Uploaded image file
        rep_phase: Optional rep phase

    Returns:
        Form analysis results
    """
    try:
        # Read file
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Get models
        models = request.app.state.models
        pose_estimator = models["pose_estimator"]
        form_analyzer = models["form_analyzer"]

        # Process
        pose_result = pose_estimator.process_frame(frame)

        if pose_result is None:
            return {
                "form_score": 0.0,
                "is_valid": False,
                "feedback": ["No person detected"],
                "angles": {},
            }

        # Analyze
        form_result = form_analyzer.analyze(
            exercise=exercise,
            landmarks=pose_result["landmarks"],
            rep_phase=rep_phase,
        )

        return form_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exercises")
async def list_exercises():
    """
    List supported exercises

    Returns:
        List of exercise names
    """
    return {
        "exercises": [
            {
                "name": "squat",
                "display_name": "Squat",
                "description": "Lower body exercise targeting quadriceps, hamstrings, glutes",
                "key_points": ["Hip depth", "Knee alignment", "Back straightness"],
            },
            {
                "name": "pushup",
                "display_name": "Push-up",
                "description": "Upper body exercise targeting chest, triceps, shoulders",
                "key_points": ["Elbow angle", "Body alignment", "Hand position"],
            },
            {
                "name": "deadlift",
                "display_name": "Deadlift",
                "description": "Full body exercise targeting back, glutes, hamstrings",
                "key_points": ["Hip hinge", "Back straightness", "Starting position"],
            },
            {
                "name": "plank",
                "display_name": "Plank",
                "description": "Core exercise for abs and stability",
                "key_points": ["Body alignment", "Hip position", "Hold time"],
            },
        ]
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "posture-analysis",
    }
