from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Severity(str, Enum):
    """Issue severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IssueDetail(BaseModel):
    """Detailed information about a form issue."""

    type: str = Field(..., description="Issue type identifier")
    severity: Severity = Field(..., description="Issue severity level")
    description: str = Field(..., description="Human-readable description")
    correction: str = Field(..., description="Corrective action suggestion")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "knee_valgus",
                "severity": "medium",
                "description": "Knees are caving inward",
                "correction": "Push knees outward, align with toes"
            }
        }


class Analysis(BaseModel):
    """Posture analysis result for a single frame."""

    exercise: str = Field(..., description="Exercise type being performed")
    score: float = Field(..., ge=0.0, le=10.0, description="Form score (0-10)")
    issues: List[IssueDetail] = Field(default_factory=list, description="Detected issues")
    is_good_form: bool = Field(..., description="Whether form meets quality threshold")
    keypoints_analyzed: int = Field(..., ge=0, description="Number of keypoints analyzed")
    timestamp: Optional[float] = Field(None, description="Analysis timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "exercise": "squat",
                "score": 8.5,
                "issues": [],
                "is_good_form": True,
                "keypoints_analyzed": 13,
                "timestamp": 1716098765.123
            }
        }

    @property
    def has_issues(self) -> bool:
        """Check if any issues were detected."""
        return len(self.issues) > 0

    @property
    def high_severity_issues(self) -> List[IssueDetail]:
        """Get only high severity issues."""
        return [issue for issue in self.issues if issue.severity == Severity.HIGH]
