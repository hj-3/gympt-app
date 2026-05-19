from pydantic import BaseModel, Field
from typing import List, Optional


class PoseLandmark(BaseModel):
    """Single pose landmark with 3D coordinates and visibility."""

    x: float = Field(..., description="X coordinate (normalized 0-1)")
    y: float = Field(..., description="Y coordinate (normalized 0-1)")
    z: float = Field(..., description="Z coordinate (depth, normalized)")
    visibility: float = Field(..., ge=0.0, le=1.0, description="Visibility score")

    class Config:
        json_schema_extra = {
            "example": {
                "x": 0.5,
                "y": 0.3,
                "z": -0.1,
                "visibility": 0.95
            }
        }


class PoseLandmarks(BaseModel):
    """Collection of 33 MediaPipe pose landmarks."""

    landmarks: List[PoseLandmark] = Field(..., min_length=33, max_length=33)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall detection confidence")

    class Config:
        json_schema_extra = {
            "example": {
                "landmarks": [{"x": 0.5, "y": 0.3, "z": -0.1, "visibility": 0.95}] * 33,
                "confidence": 0.92
            }
        }

    def get_landmark(self, index: int) -> Optional[PoseLandmark]:
        """Get landmark by index (0-32)."""
        if 0 <= index < len(self.landmarks):
            return self.landmarks[index]
        return None

    def to_dict(self):
        """Convert to dictionary format."""
        return {
            "landmarks": [lm.model_dump() for lm in self.landmarks],
            "confidence": self.confidence
        }
