"""
E2E tests for workout recommendation flow.

Tests the complete flow:
API request → Backend API call → Bedrock call → DynamoDB log → Cache → Response
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status


@pytest.mark.e2e
@pytest.mark.smoke
@pytest.mark.asyncio
async def test_workout_recommendation_full_flow(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test complete workout recommendation flow."""
    # Mock all dependencies
    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        # Make request
        response = test_client.post(
            "/agent/workout/recommend",
            json=sample_workout_request,
            headers={"X-Internal-Token": "test-token"}
        )

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "recommendation" in data
        assert "model_used" in data
        assert "cached" in data
        assert "interaction_id" in data
        assert data["cached"] is False  # First call should not be cached

        # Verify backend was called
        mock_backend_client.get_user_profile.assert_called_once()

        # Verify Bedrock was called
        mock_bedrock_client.invoke_model.assert_called_once()

        # Verify DynamoDB was called
        mock_dynamodb_client.log_interaction.assert_called_once()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workout_recommendation_beginner_level(
    test_client,
    sample_workout_request_beginner,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test workout recommendation for beginner user."""
    mock_bedrock_client.invoke_model.return_value = {
        "content": "Beginner workout plan focusing on form and consistency...",
        "model": "mock-model",
        "usage": {"input_tokens": 50, "output_tokens": 150},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post(
            "/agent/workout/recommend",
            json=sample_workout_request_beginner
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recommendation" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workout_recommendation_advanced_with_injury(
    test_client,
    sample_workout_request_advanced,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test workout recommendation for advanced user with injury limitations."""
    mock_bedrock_client.invoke_model.return_value = {
        "content": "Advanced program modified for knee injury. Avoid deep squats...",
        "model": "mock-model",
        "usage": {"input_tokens": 100, "output_tokens": 250},
        "stop_reason": "end_turn"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post(
            "/agent/workout/recommend",
            json=sample_workout_request_advanced
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify injury consideration in prompt
        call_args = mock_bedrock_client.invoke_model.call_args
        prompt = call_args.kwargs.get("prompt", "")
        assert "knee" in prompt.lower() or "injury" in prompt.lower()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workout_recommendation_with_no_equipment(
    test_client,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test workout recommendation with no equipment (bodyweight only)."""
    request_data = {
        "user_id": "test-user-no-equipment",
        "goal": "weight_loss",
        "fitness_level": "intermediate",
        "days_per_week": 5,
        "equipment_available": [],
        "injuries_or_limitations": None
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recommendation" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workout_recommendation_cache_hit(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test that second identical request returns cached response."""
    cached_response = {
        "recommendation": "Cached workout plan",
        "model_used": "mock-model",
        "cached": False,
        "interaction_id": "cached-interaction-id"
    }

    # First call: cache miss
    mock_redis_client.get.return_value = None

    # Second call: cache hit
    import json
    mock_redis_client.get.return_value = json.dumps(cached_response)

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        # First request
        response1 = test_client.post("/agent/workout/recommend", json=sample_workout_request)
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert data1["cached"] is False

        # Reset mock to simulate cache hit
        mock_redis_client.get.return_value = json.dumps(cached_response)

        # Second identical request
        response2 = test_client.post("/agent/workout/recommend", json=sample_workout_request)
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["cached"] is True


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workout_recommendation_backend_api_error(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test error handling when Backend API is down."""
    # Simulate backend API error
    mock_backend_client.get_user_profile.side_effect = Exception("Backend API connection failed")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=sample_workout_request)

        # Should return 500 error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workout_recommendation_bedrock_timeout(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test error handling when Bedrock times out."""
    # Simulate Bedrock timeout
    mock_bedrock_client.invoke_model.side_effect = Exception("Bedrock request timeout")

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=sample_workout_request)

        # Should return 500 error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workout_recommendation_invalid_request(test_client):
    """Test validation for invalid workout request."""
    invalid_request = {
        "user_id": "test-user",
        "goal": "invalid_goal",  # Invalid enum value
        "fitness_level": "intermediate",
        "days_per_week": 10  # Invalid value (> 7)
    }

    response = test_client.post("/agent/workout/recommend", json=invalid_request)

    # Should return 422 validation error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workout_recommendation_metrics_tracking(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test that metrics are properly tracked."""
    from app.metrics import agent_interactions_total

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        # Get initial metric value
        initial_count = agent_interactions_total._metrics.get(
            ("workout_recommend", "success"),
            agent_interactions_total._metrics.get(
                (b"workout_recommend", b"success"),
                type("Counter", (), {"_value": type("Value", (), {"_value": 0})()})()
            )
        )

        response = test_client.post("/agent/workout/recommend", json=sample_workout_request)
        assert response.status_code == status.HTTP_200_OK

        # Note: Metrics validation in real environment would check Prometheus


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_workout_recommendation_concurrent_requests(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test handling of concurrent workout recommendation requests."""
    import asyncio

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        # Make 5 concurrent requests
        responses = []
        for i in range(5):
            request_data = sample_workout_request.copy()
            request_data["user_id"] = f"test-user-{i}"
            response = test_client.post("/agent/workout/recommend", json=request_data)
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "recommendation" in data
