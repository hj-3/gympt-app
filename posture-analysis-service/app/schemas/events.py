from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class PostureEvent(BaseModel):
    """Posture analysis event for DynamoDB."""

    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    timestamp: float = Field(..., description="Event timestamp (Unix epoch)")
    exercise: str = Field(..., description="Exercise type")
    score: float = Field(..., ge=0.0, le=10.0, description="Form score")
    issues: List[Dict] = Field(default_factory=list, description="Issues detected")
    rep_count: int = Field(..., ge=0, description="Current rep count")
    frame_number: int = Field(..., ge=0, description="Frame sequence number")
    event_type: str = Field(default="analysis", description="Event type")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr_123",
                "session_id": "usr_123_20260519_143022",
                "timestamp": 1716098765.123,
                "exercise": "squat",
                "score": 8.5,
                "issues": [
                    {
                        "type": "knee_valgus",
                        "severity": "medium",
                        "description": "Knees are caving inward"
                    }
                ],
                "rep_count": 5,
                "frame_number": 150,
                "event_type": "analysis"
            }
        }

    def to_dynamodb_item(self) -> Dict:
        """Convert to DynamoDB item format."""
        return {
            "pk": f"{self.user_id}#{self.session_id}",
            "sk": f"TIMESTAMP#{self.timestamp}",
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "exercise": self.exercise,
            "score": self.score,
            "issues": self.issues,
            "rep_count": self.rep_count,
            "frame_number": self.frame_number,
            "event_type": self.event_type,
            "created_at": datetime.utcnow().isoformat()
        }
