from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from app.schemas.analysis import IssueDetail


class WebSocketRequest(BaseModel):
    """WebSocket client request."""

    action: str = Field(..., description="Action type: start_session, stop_session, process_frame")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    exercise_type: Optional[str] = Field(None, description="Exercise type")
    frame_data: Optional[str] = Field(None, description="Base64 encoded frame")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "start_session",
                "user_id": "usr_123",
                "exercise_type": "squat"
            }
        }


class WebSocketResponse(BaseModel):
    """Enhanced WebSocket response with rep counting and session stats."""

    status: str = Field(..., description="Response status: success, error, processing")
    session_id: Optional[str] = Field(None, description="Session identifier")
    exercise: Optional[str] = Field(None, description="Exercise type")
    score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Current form score")
    rep_count: int = Field(default=0, ge=0, description="Current rep count")
    total_reps: int = Field(default=0, ge=0, description="Total reps in session")
    avg_score: float = Field(default=0.0, ge=0.0, le=10.0, description="Average session score")
    issues: List[IssueDetail] = Field(default_factory=list, description="Current issues")
    feedback: Optional[str] = Field(None, description="Real-time feedback message")
    timestamp: Optional[float] = Field(None, description="Response timestamp")
    frame_number: int = Field(default=0, ge=0, description="Frame sequence number")
    error: Optional[str] = Field(None, description="Error message if status=error")
    session_summary: Optional[Dict[str, Any]] = Field(None, description="Summary when session ends")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "session_id": "usr_123_20260519_143022",
                "exercise": "squat",
                "score": 8.5,
                "rep_count": 5,
                "total_reps": 5,
                "avg_score": 8.7,
                "issues": [],
                "feedback": "Great form! Keep it up.",
                "timestamp": 1716098765.123,
                "frame_number": 150
            }
        }
