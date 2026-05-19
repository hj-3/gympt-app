import pytest
from app.feedback.feedback_service import FeedbackService


@pytest.mark.asyncio
async def test_generate_feedback_excellent():
    """Test feedback generation for excellent form."""
    service = FeedbackService()
    
    analysis = {
        "score": 9.5,
        "issues": []
    }
    
    feedback = await service.generate_feedback(analysis)
    
    assert feedback["priority"] == "maintain"
    assert feedback["score"] == 9.5
    assert "Excellent" in feedback["overall"]


@pytest.mark.asyncio
async def test_generate_feedback_with_issues():
    """Test feedback generation with form issues."""
    service = FeedbackService()
    
    analysis = {
        "score": 6.0,
        "issues": [
            {
                "type": "knee_valgus",
                "severity": "medium",
                "description": "Knees caving in",
                "correction": "Push knees out"
            }
        ]
    }
    
    feedback = await service.generate_feedback(analysis)
    
    assert feedback["priority"] == "correct"
    assert len(feedback["corrections"]) == 1
    assert feedback["corrections"][0]["issue"] == "knee_valgus"


@pytest.mark.asyncio
async def test_generate_feedback_urgent():
    """Test feedback for urgent correction."""
    service = FeedbackService()
    
    analysis = {
        "score": 3.0,
        "issues": [
            {
                "type": "back_rounding",
                "severity": "high",
                "description": "Dangerous back position",
                "correction": "Stop immediately"
            }
        ]
    }
    
    feedback = await service.generate_feedback(analysis)
    
    assert feedback["priority"] == "urgent"
    assert "Stop" in feedback["overall"] or "immediately" in feedback["overall"]
