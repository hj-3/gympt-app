"""
API Routes for Agent Service
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from ..services.bedrock_agent_service import BedrockAgentService

router = APIRouter()


class AgentRequest(BaseModel):
    """Agent request model"""

    user_id: str
    session_id: str
    input_text: str
    context: Optional[Dict[str, Any]] = None


class WorkoutPlanRequest(BaseModel):
    """Workout plan generation request"""

    user_id: str
    session_id: str
    user_profile: Dict[str, Any]
    goals: List[str]
    constraints: Optional[Dict[str, Any]] = None


class PostureFeedbackRequest(BaseModel):
    """Posture feedback request"""

    user_id: str
    session_id: str
    exercise: str
    posture_data: Dict[str, Any]
    rep_count: int
    previous_feedback: Optional[List[Dict[str, Any]]] = None


class ReportRequest(BaseModel):
    """Workout report generation request"""

    user_id: str
    session_id: str
    workout_summary: Dict[str, Any]
    historical_data: Optional[List[Dict[str, Any]]] = None


class AgentResponse(BaseModel):
    """Agent response model"""

    session_id: str
    output_text: str
    completion: bool
    citations: Optional[list] = None
    trace: Optional[Dict[str, Any]] = None


def get_agent_service():
    """Dependency injection for agent service"""
    return BedrockAgentService()


@router.post("/agent/invoke", response_model=AgentResponse)
async def invoke_agent(
    request: AgentRequest,
    agent_service: BedrockAgentService = Depends(get_agent_service),
):
    """
    Invoke Bedrock Agent with user input
    """
    try:
        response = await agent_service.invoke_agent(
            user_id=request.user_id,
            session_id=request.session_id,
            input_text=request.input_text,
            context=request.context,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/workout-plan", response_model=AgentResponse)
async def generate_workout_plan(
    request: WorkoutPlanRequest,
    agent_service: BedrockAgentService = Depends(get_agent_service),
):
    """
    Generate personalized workout plan using AI agent with RAG
    """
    try:
        response = await agent_service.generate_workout_plan(
            user_id=request.user_id,
            session_id=request.session_id,
            user_profile=request.user_profile,
            goals=request.goals,
            constraints=request.constraints,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/posture-feedback", response_model=AgentResponse)
async def analyze_posture(
    request: PostureFeedbackRequest,
    agent_service: BedrockAgentService = Depends(get_agent_service),
):
    """
    Get real-time posture feedback from AI agent
    """
    try:
        response = await agent_service.analyze_posture_feedback(
            user_id=request.user_id,
            session_id=request.session_id,
            exercise=request.exercise,
            posture_data=request.posture_data,
            rep_count=request.rep_count,
            previous_feedback=request.previous_feedback,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/report", response_model=AgentResponse)
async def generate_report(
    request: ReportRequest,
    agent_service: BedrockAgentService = Depends(get_agent_service),
):
    """
    Generate comprehensive workout report with AI insights
    """
    try:
        response = await agent_service.generate_workout_report(
            user_id=request.user_id,
            session_id=request.session_id,
            workout_summary=request.workout_summary,
            historical_data=request.historical_data,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/chat", response_model=AgentResponse)
async def chat_with_agent(
    request: AgentRequest,
    agent_service: BedrockAgentService = Depends(get_agent_service),
):
    """
    Interactive chat with PT AI Agent (with conversation memory)
    """
    try:
        response = await agent_service.chat_interactive(
            user_id=request.user_id,
            session_id=request.session_id,
            user_message=request.input_text,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent-service"}
