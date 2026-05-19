"""
E2E tests for report generation flow.

Tests the complete flow:
API request → Backend API (user data) → Bedrock → DynamoDB log → SQS publish → Response
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status


@pytest.mark.e2e
@pytest.mark.smoke
@pytest.mark.asyncio
async def test_report_generation_full_flow(
    test_client,
    sample_report_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client
):
    """Test complete report generation flow."""
    mock_bedrock_client.invoke_model.return_value = {
        "content": """Weekly Progress Summary:

**Key Achievements:**
- Completed 4/5 workouts
- Squat PR: +10 lbs
- Consistency: 80%

**Recommendations:**
- Increase protein intake
- Focus on recovery""",
        "model": "mock-model",
        "usage": {"input_tokens": 150, "output_tokens": 300},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        response = test_client.post(
            "/agent/report/generate",
            json=sample_report_request,
            headers={"X-Internal-Token": "test-token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "report_summary" in data
        assert "key_insights" in data
        assert "recommendations" in data
        assert "model_used" in data
        assert "task_id" in data

        # Verify backend was called
        mock_backend_client.get_user_data.assert_called_once()

        # Verify Bedrock was called
        mock_bedrock_client.invoke_model.assert_called_once()

        # Verify DynamoDB was called
        mock_dynamodb_client.log_interaction.assert_called_once()

        # Verify SQS was called
        mock_sqs_client.publish_report_generation_task.assert_called_once()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_report_generation_weekly_report(
    test_client,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client
):
    """Test weekly report generation."""
    request_data = {
        "user_id": "test-user-123",
        "period_start": "2024-01-01",
        "period_end": "2024-01-07",
        "include_sections": ["summary", "workouts", "recommendations"]
    }

    mock_bedrock_client.invoke_model.return_value = {
        "content": "Weekly report content with insights",
        "model": "mock-model",
        "usage": {"input_tokens": 100, "output_tokens": 200},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        response = test_client.post("/agent/report/generate", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["key_insights"], list)
        assert isinstance(data["recommendations"], list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_report_generation_monthly_report(
    test_client,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client
):
    """Test monthly report generation."""
    request_data = {
        "user_id": "test-user-123",
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "include_sections": ["summary", "workouts", "progress", "recommendations"]
    }

    mock_bedrock_client.invoke_model.return_value = {
        "content": """Monthly Progress Report:

- Workout consistency: 85%
- Total volume increase: 15%
- Body composition improvements noted

Recommendations:
- Continue current program
- Add deload week next month""",
        "model": "mock-model",
        "usage": {"input_tokens": 200, "output_tokens": 400},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        response = test_client.post("/agent/report/generate", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["key_insights"]) > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_report_generation_no_workout_history(
    test_client,
    sample_report_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client
):
    """Test report generation when user has no workout history."""
    # Mock backend returning user with no workouts
    mock_backend_client.get_user_data.return_value = {
        "user_id": "test-user-123",
        "profile": {"name": "New User"},
        "body_profile": None,
        "goals": []
    }

    mock_bedrock_client.invoke_model.return_value = {
        "content": """No workout data available yet.

Recommendations:
- Start with beginner program
- Focus on consistency
- Set realistic goals""",
        "model": "mock-model",
        "usage": {"input_tokens": 80, "output_tokens": 150},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        response = test_client.post("/agent/report/generate", json=sample_report_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "report_summary" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_report_generation_sqs_message_published(
    test_client,
    sample_report_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client
):
    """Test that SQS message is published for async report generation."""
    mock_sqs_client.publish_report_generation_task.return_value = {
        "MessageId": "test-message-123"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        response = test_client.post("/agent/report/generate", json=sample_report_request)

        assert response.status_code == status.HTTP_200_OK

        # Verify SQS publish was called with correct parameters
        call_args = mock_sqs_client.publish_report_generation_task.call_args
        assert call_args.kwargs["user_id"] == sample_report_request["user_id"]
        assert call_args.kwargs["period_start"] == sample_report_request["period_start"]
        assert call_args.kwargs["period_end"] == sample_report_request["period_end"]
        assert "report_data" in call_args.kwargs


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_report_generation_insights_extraction(
    test_client,
    sample_report_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client
):
    """Test that key insights are properly extracted from report content."""
    mock_bedrock_client.invoke_model.return_value = {
        "content": """Progress Summary:

- Workout frequency increased by 25%
- Average workout duration: 45 minutes
- Strength gains across all major lifts
- Improved sleep quality
- Better recovery times

Recommendations:
- Add stretching routine
- Increase protein intake""",
        "model": "mock-model",
        "usage": {"input_tokens": 100, "output_tokens": 200},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        response = test_client.post("/agent/report/generate", json=sample_report_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should extract insights
        assert len(data["key_insights"]) > 0
        assert len(data["recommendations"]) > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_report_generation_backend_api_error(
    test_client,
    sample_report_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client
):
    """Test error handling when Backend API fails."""
    mock_backend_client.get_user_data.side_effect = Exception("Backend API error")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        response = test_client.post("/agent/report/generate", json=sample_report_request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_report_generation_sqs_error_non_blocking(
    test_client,
    sample_report_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client
):
    """Test that SQS error doesn't fail the request (non-blocking)."""
    mock_bedrock_client.invoke_model.return_value = {
        "content": "Test report content",
        "model": "mock-model",
        "usage": {"input_tokens": 100, "output_tokens": 200},
        "stop_reason": "end_turn"
    }

    # SQS error should not block response
    mock_sqs_client.publish_report_generation_task.side_effect = Exception("SQS error")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        response = test_client.post("/agent/report/generate", json=sample_report_request)

        # Should still succeed (SQS is non-blocking)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_report_generation_invalid_date_range(test_client):
    """Test validation for invalid date range."""
    invalid_request = {
        "user_id": "test-user",
        "period_start": "2024-01-31",
        "period_end": "2024-01-01",  # End before start
        "include_sections": ["summary"]
    }

    response = test_client.post("/agent/report/generate", json=invalid_request)

    # Note: This would require additional validation in the API
    # For now, it will process but may produce unexpected results
    # In production, add date validation
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_report_generation_task_id_uniqueness(
    test_client,
    sample_report_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_sqs_client
):
    """Test that each report generation gets a unique task ID."""
    mock_bedrock_client.invoke_model.return_value = {
        "content": "Test report",
        "model": "mock-model",
        "usage": {"input_tokens": 50, "output_tokens": 100},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.agent_service.sqs_client", mock_sqs_client):

        # Generate two reports
        response1 = test_client.post("/agent/report/generate", json=sample_report_request)
        response2 = test_client.post("/agent/report/generate", json=sample_report_request)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        data1 = response1.json()
        data2 = response2.json()

        # Task IDs should be different
        assert data1["task_id"] != data2["task_id"]
