from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


class SessionState(str, Enum):
    """Session state."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionSummary(BaseModel):
    """Summary of a completed analysis session."""

    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    exercise_type: str = Field(..., description="Exercise performed")
    total_reps: int = Field(..., ge=0, description="Total repetitions completed")
    avg_score: float = Field(..., ge=0.0, le=10.0, description="Average form score")
    duration_seconds: float = Field(..., ge=0.0, description="Session duration")
    issues_detected: int = Field(..., ge=0, description="Total issues detected")
    issues_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Issue counts by type"
    )
    started_at: datetime = Field(..., description="Session start time")
    ended_at: Optional[datetime] = Field(None, description="Session end time")
    state: SessionState = Field(default=SessionState.COMPLETED)
    total_frames_processed: int = Field(default=0, ge=0)
    s3_result_key: Optional[str] = Field(None, description="S3 key for detailed results")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "usr_123_20260519_143022",
                "user_id": "usr_123",
                "exercise_type": "squat",
                "total_reps": 15,
                "avg_score": 8.3,
                "duration_seconds": 180.5,
                "issues_detected": 3,
                "issues_summary": {"knee_valgus": 2, "insufficient_depth": 1},
                "started_at": "2026-05-19T14:30:22Z",
                "ended_at": "2026-05-19T14:33:22Z",
                "state": "completed",
                "total_frames_processed": 1805,
                "s3_result_key": "usr_123/usr_123_20260519_143022/results.json"
            }
        }


class SessionMetrics(BaseModel):
    """Real-time session metrics."""

    session_id: str
    current_reps: int = 0
    current_score: float = 0.0
    frames_processed: int = 0
    issues_count: int = 0
    elapsed_seconds: float = 0.0
    last_rep_at: Optional[datetime] = None
