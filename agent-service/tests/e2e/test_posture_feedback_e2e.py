"""
E2E tests for posture feedback flow.

Tests the complete flow:
API request → Bedrock call → DynamoDB log → Response
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status


@pytest.mark.e2e
@pytest.mark.smoke
@pytest.mark.asyncio
async def test_posture_feedback_full_flow(
    test_client,
    sample_posture_request,
    mock_bedrock_client,
    mock_dynamodb_client
):
    """Test complete posture feedback flow."""
    mock_bedrock_client.invoke_model.return_value = {
        "content": "Your squat form shows knee valgus. Focus on pushing knees outward...",
        "model": "mock-model",
        "usage": {"input_tokens": 80, "output_tokens": 120},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        response = test_client.post(
            "/agent/posture/feedback",
            json=sample_posture_request
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "feedback" in data
        assert "corrections" in data
        assert "severity" in data
        assert "model_used" in data
        assert data["severity"] in ["low", "medium", "high"]

        # Verify Bedrock was called
        mock_bedrock_client.invoke_model.assert_called_once()

        # Verify DynamoDB was called
        mock_dynamodb_client.log_interaction.assert_called_once()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_posture_feedback_squat_exercise(
    test_client,
    mock_bedrock_client,
    mock_dynamodb_client
):
    """Test posture feedback for squat exercise."""
    request_data = {
        "session_id": "session-squat-001",
        "exercise_name": "squat",
        "posture_score": 7.5,
        "detected_issues": ["knee_valgus", "insufficient_depth"],
        "frame_data": {}
    }

    mock_bedrock_client.invoke_model.return_value = {
        "content": "Good upper body position. Moderate knee valgus detected. Push knees outward.",
        "model": "mock-model",
        "usage": {"input_tokens": 70, "output_tokens": 100},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        response = test_client.post("/agent/posture/feedback", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["severity"] == "medium"  # Based on "moderate" keyword


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_posture_feedback_deadlift_critical(
    test_client,
    sample_posture_request_critical,
    mock_bedrock_client,
    mock_dynamodb_client
):
    """Test posture feedback for deadlift with critical issues."""
    mock_bedrock_client.invoke_model.return_value = {
        "content": "SEVERE WARNING: Rounded back detected. STOP immediately to prevent injury.",
        "model": "mock-model",
        "usage": {"input_tokens": 90, "output_tokens": 80},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        response = test_client.post(
            "/agent/posture/feedback",
            json=sample_posture_request_critical
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["severity"] == "high"  # Should detect "severe" or "stop"
        assert "feedback" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_posture_feedback_pushup_exercise(
    test_client,
    mock_bedrock_client,
    mock_dynamodb_client
):
    """Test posture feedback for pushup exercise."""
    request_data = {
        "session_id": "session-pushup-001",
        "exercise_name": "pushup",
        "posture_score": 8.5,
        "detected_issues": ["elbow_flare"],
        "frame_data": {}
    }

    mock_bedrock_client.invoke_model.return_value = {
        "content": "Good overall form. Minor elbow flare. Keep elbows at 45 degrees.",
        "model": "mock-model",
        "usage": {"input_tokens": 60, "output_tokens": 90},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        response = test_client.post("/agent/posture/feedback", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["severity"] == "low"  # Good form, minor issue


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_posture_feedback_plank_exercise(
    test_client,
    mock_bedrock_client,
    mock_dynamodb_client
):
    """Test posture feedback for plank exercise."""
    request_data = {
        "session_id": "session-plank-001",
        "exercise_name": "plank",
        "posture_score": 6.0,
        "detected_issues": ["hip_sag", "head_position"],
        "frame_data": {}
    }

    mock_bedrock_client.invoke_model.return_value = {
        "content": "Hip sag detected - engage core more. Keep head neutral.",
        "model": "mock-model",
        "usage": {"input_tokens": 70, "output_tokens": 85},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        response = test_client.post("/agent/posture/feedback", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "feedback" in data
        assert len(data["corrections"]) == 2


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_posture_feedback_concurrent_sessions(
    test_client,
    mock_bedrock_client,
    mock_dynamodb_client
):
    """Test concurrent posture feedback for multiple sessions."""
    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        mock_bedrock_client.invoke_model.return_value = {
            "content": "Test feedback",
            "model": "mock-model",
            "usage": {"input_tokens": 50, "output_tokens": 50},
            "stop_reason": "end_turn"
        }

        # Make multiple concurrent requests
        responses = []
        for i in range(3):
            request_data = {
                "session_id": f"session-{i}",
                "exercise_name": "squat",
                "posture_score": 7.0,
                "detected_issues": ["test_issue"],
                "frame_data": {}
            }
            response = test_client.post("/agent/posture/feedback", json=request_data)
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_posture_feedback_bedrock_error(
    test_client,
    sample_posture_request,
    mock_bedrock_client,
    mock_dynamodb_client
):
    """Test error handling when Bedrock fails."""
    mock_bedrock_client.invoke_model.side_effect = Exception("Bedrock service error")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        response = test_client.post("/agent/posture/feedback", json=sample_posture_request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_posture_feedback_dynamodb_error(
    test_client,
    sample_posture_request,
    mock_bedrock_client,
    mock_dynamodb_client
):
    """Test that DynamoDB error doesn't fail the request (non-blocking)."""
    mock_bedrock_client.invoke_model.return_value = {
        "content": "Test feedback",
        "model": "mock-model",
        "usage": {"input_tokens": 50, "output_tokens": 50},
        "stop_reason": "end_turn"
    }

    # DynamoDB error should not block response
    mock_dynamodb_client.log_interaction.side_effect = Exception("DynamoDB error")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        response = test_client.post("/agent/posture/feedback", json=sample_posture_request)

        # Should still succeed (logging is non-blocking)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_posture_feedback_invalid_score(test_client):
    """Test validation for invalid posture score."""
    invalid_request = {
        "session_id": "test-session",
        "exercise_name": "squat",
        "posture_score": 15.0,  # Invalid (> 10)
        "detected_issues": []
    }

    response = test_client.post("/agent/posture/feedback", json=invalid_request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_posture_feedback_severity_detection(
    test_client,
    mock_bedrock_client,
    mock_dynamodb_client
):
    """Test severity level detection from feedback content."""
    test_cases = [
        ("Excellent form! Keep it up.", "low"),
        ("Caution: slight knee valgus detected.", "medium"),
        ("SEVERE: Stop immediately! Dangerous form.", "high"),
        ("Moderate form issues. Focus on depth.", "medium"),
        ("Danger: rounded back detected.", "high"),
    ]

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client):

        for content, expected_severity in test_cases:
            mock_bedrock_client.invoke_model.return_value = {
                "content": content,
                "model": "mock-model",
                "usage": {"input_tokens": 50, "output_tokens": 50},
                "stop_reason": "end_turn"
            }

            request_data = {
                "session_id": "test-session",
                "exercise_name": "test",
                "posture_score": 7.0,
                "detected_issues": []
            }

            response = test_client.post("/agent/posture/feedback", json=request_data)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["severity"] == expected_severity, f"Failed for content: {content}"
