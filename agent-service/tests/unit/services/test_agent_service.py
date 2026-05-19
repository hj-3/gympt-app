"""
Unit tests for AgentService.

Tests all agent service methods with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_workout_plan_success(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client,
    sample_workout_request
):
    """Test successful workout plan generation."""
    from app.services.agent_service import AgentService

    service = AgentService()

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        result = await service.generate_workout_plan(
            user_id="test-user-123",
            workout_request=sample_workout_request,
            internal_token="test-token"
        )

        assert result is not None
        assert "recommendation" in result
        assert "model_used" in result
        assert "cached" in result
        assert "interaction_id" in result
        assert result["cached"] is False

        mock_backend_client.get_user_profile.assert_called_once()
        mock_bedrock_client.invoke_model.assert_called_once()
        mock_dynamodb_client.log_interaction.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_workout_plan_with_cache_hit(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client,
    sample_workout_request
):
    """Test workout plan generation with cache hit."""
    from app.services.agent_service import AgentService
    import json

    service = AgentService()

    cached_response = {
        "recommendation": "Cached workout plan",
        "model_used": "cached-model",
        "cached": False,
        "interaction_id": "cached-id"
    }

    mock_redis_client.get.return_value = json.dumps(cached_response)

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        result = await service.generate_workout_plan(
            user_id="test-user-123",
            workout_request=sample_workout_request
        )

        assert result["cached"] is True
        # Should not call Bedrock or Backend on cache hit
        mock_bedrock_client.invoke_model.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_workout_plan_backend_error(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client,
    sample_workout_request
):
    """Test workout plan generation when Backend API fails."""
    from app.services.agent_service import AgentService

    service = AgentService()

    mock_backend_client.get_user_profile.side_effect = Exception("Backend API error")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        with pytest.raises(Exception) as exc_info:
            await service.generate_workout_plan(
                user_id="test-user-123",
                workout_request=sample_workout_request
            )

        assert "Backend API error" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_workout_plan_bedrock_error(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client,
    sample_workout_request
):
    """Test workout plan generation when Bedrock fails."""
    from app.services.agent_service import AgentService

    service = AgentService()

    mock_bedrock_client.invoke_model.side_effect = Exception("Bedrock error")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        with pytest.raises(Exception) as exc_info:
            await service.generate_workout_plan(
                user_id="test-user-123",
                workout_request=sample_workout_request
            )

        assert "Bedrock error" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_posture_feedback_success(
    mock_bedrock_client,
    mock_dynamodb_client,
    sample_posture_request
):
    """Test successful posture feedback generation."""
    from app.services.agent_service import AgentService

    service = AgentService()

    mock_bedrock_client.invoke_model.return_value = {
        "content": "Good form overall. Minor corrections needed.",
        "model": "test-model",
        "usage": {"input_tokens": 50, "output_tokens": 100},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        result = await service.generate_posture_feedback(
            user_id="test-user-123",
            posture_request=sample_posture_request
        )

        assert result is not None
        assert "feedback" in result
        assert "corrections" in result
        assert "severity" in result
        assert result["severity"] in ["low", "medium", "high"]

        mock_bedrock_client.invoke_model.assert_called_once()
        mock_dynamodb_client.log_interaction.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_posture_feedback_severity_low(
    mock_bedrock_client,
    mock_dynamodb_client,
    sample_posture_request
):
    """Test posture feedback with low severity."""
    from app.services.agent_service import AgentService

    service = AgentService()

    mock_bedrock_client.invoke_model.return_value = {
        "content": "Excellent form! Keep up the good work.",
        "model": "test-model",
        "usage": {},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        result = await service.generate_posture_feedback(
            user_id="test-user",
            posture_request=sample_posture_request
        )

        assert result["severity"] == "low"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_posture_feedback_severity_high(
    mock_bedrock_client,
    mock_dynamodb_client,
    sample_posture_request
):
    """Test posture feedback with high severity."""
    from app.services.agent_service import AgentService

    service = AgentService()

    mock_bedrock_client.invoke_model.return_value = {
        "content": "SEVERE WARNING: STOP immediately! Dangerous form detected.",
        "model": "test-model",
        "usage": {},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        result = await service.generate_posture_feedback(
            user_id="test-user",
            posture_request=sample_posture_request
        )

        assert result["severity"] == "high"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_posture_feedback_dynamodb_error(
    mock_bedrock_client,
    mock_dynamodb_client,
    sample_posture_request
):
    """Test posture feedback when DynamoDB logging fails."""
    from app.services.agent_service import AgentService

    service = AgentService()

    mock_bedrock_client.invoke_model.return_value = {
        "content": "Test feedback",
        "model": "test-model",
        "usage": {},
        "stop_reason": "end_turn"
    }

    mock_dynamodb_client.log_interaction.side_effect = Exception("DynamoDB error")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        with pytest.raises(Exception):
            await service.generate_posture_feedback(
                user_id="test-user",
                posture_request=sample_posture_request
            )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_report_success(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client,
    sample_report_request
):
    """Test successful report generation."""
    from app.services.agent_service import AgentService

    service = AgentService()

    mock_bedrock_client.invoke_model.return_value = {
        "content": """Progress Summary:

- Workout frequency increased
- Strength gains noted
- Good consistency

Recommendations:
- Add deload week
- Increase protein""",
        "model": "test-model",
        "usage": {"input_tokens": 100, "output_tokens": 200},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        result = await service.generate_report(
            user_id="test-user-123",
            report_request=sample_report_request,
            internal_token="test-token"
        )

        assert result is not None
        assert "report_summary" in result
        assert "key_insights" in result
        assert "recommendations" in result
        assert "task_id" in result

        mock_backend_client.get_user_data.assert_called_once()
        mock_bedrock_client.invoke_model.assert_called_once()
        mock_dynamodb_client.log_interaction.assert_called_once()
        mock_sqs_client.publish_report_generation_task.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_report_sqs_error(
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client,
    sample_report_request
):
    """Test report generation when SQS publish fails."""
    from app.services.agent_service import AgentService

    service = AgentService()

    mock_bedrock_client.invoke_model.return_value = {
        "content": "Test report",
        "model": "test-model",
        "usage": {},
        "stop_reason": "end_turn"
    }

    mock_sqs_client.publish_report_generation_task.side_effect = Exception("SQS error")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        with pytest.raises(Exception):
            await service.generate_report(
                user_id="test-user",
                report_request=sample_report_request
            )


@pytest.mark.unit
def test_extract_insights():
    """Test insights extraction from report content."""
    from app.services.agent_service import AgentService

    service = AgentService()

    content = """Weekly Summary:

- Completed 4 workouts
- Total volume: 15,000 lbs
- Consistency: 80%
- New PR on squat
- Improved sleep quality

Good progress overall."""

    insights = service._extract_insights(content)

    assert len(insights) > 0
    assert len(insights) <= 5  # Max 5 insights


@pytest.mark.unit
def test_extract_recommendations():
    """Test recommendations extraction from report content."""
    from app.services.agent_service import AgentService

    service = AgentService()

    content = """Progress Summary:

Good consistency this week.

Recommendations:
- Increase training frequency
- Add accessory work
- Focus on nutrition
- Improve sleep schedule
- Schedule deload week

Keep up the good work!"""

    recommendations = service._extract_recommendations(content)

    assert len(recommendations) > 0
    assert len(recommendations) <= 5  # Max 5 recommendations
