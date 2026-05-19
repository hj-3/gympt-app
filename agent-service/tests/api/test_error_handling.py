"""
Tests for error handling across all API endpoints.
"""
import pytest
from fastapi import status
from unittest.mock import patch


@pytest.mark.unit
def test_404_not_found(test_client):
    """Test 404 error for non-existent endpoint."""
    response = test_client.get("/nonexistent/endpoint")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
def test_405_method_not_allowed(test_client):
    """Test 405 error for wrong HTTP method."""
    response = test_client.get("/agent/workout/recommend")  # Should be POST

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.unit
def test_422_validation_error_missing_fields(test_client):
    """Test 422 validation error for missing required fields."""
    response = test_client.post("/agent/workout/recommend", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()

    assert "detail" in data
    assert isinstance(data["detail"], list)


@pytest.mark.unit
def test_422_validation_error_invalid_type(test_client):
    """Test 422 validation error for invalid field type."""
    request = {
        "user_id": "test-user",
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": "three"  # Should be int
    }

    response = test_client.post("/agent/workout/recommend", json=request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_500_internal_server_error(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test 500 error for internal server error."""
    # Mock service to raise exception
    mock_bedrock_client.invoke_model.side_effect = Exception("Internal error")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=sample_workout_request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data


@pytest.mark.unit
def test_error_response_format_validation(test_client):
    """Test error response has consistent format."""
    response = test_client.post("/agent/workout/recommend", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()

    # FastAPI returns validation errors in 'detail'
    assert "detail" in data


@pytest.mark.unit
def test_error_response_format_500(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test 500 error response format."""
    mock_bedrock_client.invoke_model.side_effect = Exception("Test error")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=sample_workout_request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()

        assert "detail" in data
        assert isinstance(data["detail"], str)


@pytest.mark.unit
def test_invalid_json_payload(test_client):
    """Test error handling for invalid JSON payload."""
    response = test_client.post(
        "/agent/workout/recommend",
        data="invalid json {",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_posture_feedback_validation_error(test_client):
    """Test validation error for posture feedback endpoint."""
    invalid_request = {
        "session_id": "test-session",
        "exercise_name": "squat",
        "posture_score": 15.0,  # Invalid (> 10)
        "detected_issues": []
    }

    response = test_client.post("/agent/posture/feedback", json=invalid_request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_report_generation_validation_error(test_client):
    """Test validation error for report generation endpoint."""
    invalid_request = {
        "user_id": "test-user"
        # Missing period_start and period_end
    }

    response = test_client.post("/agent/report/generate", json=invalid_request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_content_type_validation(test_client):
    """Test that non-JSON content type is rejected."""
    response = test_client.post(
        "/agent/workout/recommend",
        data="key=value",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # Should return error (expecting JSON)
    assert response.status_code in [
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    ]


@pytest.mark.unit
def test_large_payload_handling(test_client):
    """Test handling of unusually large payloads."""
    request = {
        "user_id": "test-user",
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 3,
        "injuries_or_limitations": "x" * 10000  # Very long string
    }

    # Should either accept or reject gracefully
    response = test_client.post("/agent/workout/recommend", json=request)

    # Should not crash
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        status.HTTP_500_INTERNAL_SERVER_ERROR
    ]


@pytest.mark.unit
def test_special_characters_in_input(
    test_client,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test handling of special characters in input."""
    request = {
        "user_id": "test-user-123",
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 3,
        "injuries_or_limitations": "Test <script>alert('xss')</script> & special chars"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=request)

        # Should handle special characters safely
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
def test_unicode_characters_in_input(
    test_client,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test handling of unicode characters in input."""
    request = {
        "user_id": "테스트-사용자",
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 3,
        "injuries_or_limitations": "무릎 통증, スクワット避ける"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=request)

        # Should handle unicode gracefully
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
def test_error_logging(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client,
    caplog
):
    """Test that errors are properly logged."""
    import logging

    caplog.set_level(logging.ERROR)

    mock_bedrock_client.invoke_model.side_effect = Exception("Test error for logging")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=sample_workout_request)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Check that error was logged
        assert any("error" in record.message.lower() or "fail" in record.message.lower()
                   for record in caplog.records)
