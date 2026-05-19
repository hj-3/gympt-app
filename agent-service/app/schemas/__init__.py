from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class FitnessGoal(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    ENDURANCE = "endurance"
    FLEXIBILITY = "flexibility"
    GENERAL_FITNESS = "general_fitness"


class FitnessLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class WorkoutRecommendationRequest(BaseModel):
    user_id: str = Field(..., description="User UUID")
    goal: FitnessGoal = Field(..., description="Fitness goal")
    fitness_level: FitnessLevel = Field(..., description="Current fitness level")
    days_per_week: int = Field(3, ge=1, le=7, description="Workout frequency")
    equipment_available: List[str] = Field(default_factory=list, description="Available equipment")
    injuries_or_limitations: Optional[str] = Field(None, description="Medical considerations")


class WorkoutRecommendationResponse(BaseModel):
    recommendation: str = Field(..., description="AI-generated workout plan")
    model_used: str = Field(..., description="Bedrock model ID")
    cached: bool = Field(False, description="Was response cached")
    interaction_id: str = Field(..., description="Interaction tracking ID")


class PostureFeedbackRequest(BaseModel):
    session_id: str = Field(..., description="Workout session ID")
    exercise_name: str = Field(..., description="Exercise being performed")
    posture_score: float = Field(..., ge=0, le=10, description="Posture quality score")
    detected_issues: List[str] = Field(..., description="Detected form issues")
    frame_data: Optional[Dict[str, Any]] = Field(None, description="Pose landmark data")


class PostureFeedbackResponse(BaseModel):
    feedback: str = Field(..., description="AI-generated feedback")
    corrections: List[str] = Field(..., description="Specific corrections")
    severity: str = Field(..., description="Issue severity: low, medium, high")
    model_used: str = Field(..., description="Bedrock model ID")


class ReportGenerationRequest(BaseModel):
    user_id: str = Field(..., description="User UUID")
    period_start: str = Field(..., description="Report period start (ISO format)")
    period_end: str = Field(..., description="Report period end (ISO format)")
    include_sections: List[str] = Field(
        default_factory=lambda: ["summary", "workouts", "progress", "recommendations"],
        description="Report sections to include"
    )


class ReportGenerationResponse(BaseModel):
    report_summary: str = Field(..., description="Executive summary")
    key_insights: List[str] = Field(..., description="Key findings")
    recommendations: List[str] = Field(..., description="Personalized recommendations")
    model_used: str = Field(..., description="Bedrock model ID")
    task_id: str = Field(..., description="Async task ID for full report")


class IntensityAdjustRequest(BaseModel):
    user_id: str = Field(..., description="User UUID")
    recent_sessions: List[Dict[str, Any]] = Field(..., description="Recent workout data")
    feedback: str = Field(..., description="User feedback (too easy/hard)")


class IntensityAdjustResponse(BaseModel):
    adjustment: str = Field(..., description="Recommended intensity adjustment")
    rationale: str = Field(..., description="Explanation for adjustment")
    specific_changes: Dict[str, Any] = Field(..., description="Specific parameter changes")


# Backend API models
class UserProfile(BaseModel):
    user_id: str = Field(..., description="User UUID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    age: Optional[int] = Field(None, description="User age")
    gender: Optional[str] = Field(None, description="User gender")
    fitness_experience: Optional[str] = Field(None, description="Fitness experience level")
    created_at: Optional[str] = Field(None, description="Account creation date")


class BodyProfile(BaseModel):
    user_id: str = Field(..., description="User UUID")
    height_cm: Optional[float] = Field(None, description="Height in cm")
    weight_kg: Optional[float] = Field(None, description="Weight in kg")
    body_fat_percentage: Optional[float] = Field(None, description="Body fat percentage")
    muscle_mass_kg: Optional[float] = Field(None, description="Muscle mass in kg")
    measurements: Optional[Dict[str, float]] = Field(None, description="Body measurements")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")


class WorkoutGoal(BaseModel):
    goal_id: str = Field(..., description="Goal UUID")
    user_id: str = Field(..., description="User UUID")
    goal_type: str = Field(..., description="Goal type (weight_loss, muscle_gain, etc)")
    target_value: Optional[float] = Field(None, description="Target value")
    current_value: Optional[float] = Field(None, description="Current value")
    deadline: Optional[str] = Field(None, description="Goal deadline")
    status: str = Field(..., description="Goal status")
    created_at: Optional[str] = Field(None, description="Creation date")
