"""
Tests for workout recommendation API endpoint.
"""
import pytest
from fastapi import status
from unittest.mock import patch


@pytest.mark.unit
def test_workout_recommendation_request_validation(test_client):
    """Test request validation for workout recommendation."""
    # Missing required fields
    invalid_request = {
        "user_id": "test-user"
        # Missing goal, fitness_level
    }

    response = test_client.post("/agent/workout/recommend", json=invalid_request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data


@pytest.mark.unit
def test_workout_recommendation_invalid_goal(test_client):
    """Test validation for invalid goal enum."""
    invalid_request = {
        "user_id": "test-user-123",
        "goal": "invalid_goal_type",
        "fitness_level": "intermediate",
        "days_per_week": 3
    }

    response = test_client.post("/agent/workout/recommend", json=invalid_request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_workout_recommendation_invalid_fitness_level(test_client):
    """Test validation for invalid fitness level."""
    invalid_request = {
        "user_id": "test-user-123",
        "goal": "muscle_gain",
        "fitness_level": "super_expert",  # Invalid
        "days_per_week": 3
    }

    response = test_client.post("/agent/workout/recommend", json=invalid_request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_workout_recommendation_invalid_days_per_week(test_client):
    """Test validation for invalid days per week."""
    invalid_request = {
        "user_id": "test-user-123",
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 10  # Invalid (> 7)
    }

    response = test_client.post("/agent/workout/recommend", json=invalid_request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_workout_recommendation_response_schema(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test response schema for workout recommendation."""
    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=sample_workout_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response schema
        required_fields = ["recommendation", "model_used", "cached", "interaction_id"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        # Verify field types
        assert isinstance(data["recommendation"], str)
        assert isinstance(data["model_used"], str)
        assert isinstance(data["cached"], bool)
        assert isinstance(data["interaction_id"], str)


@pytest.mark.unit
def test_workout_recommendation_optional_fields(
    test_client,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test workout recommendation with optional fields."""
    request = {
        "user_id": "test-user-123",
        "goal": "weight_loss",
        "fitness_level": "beginner",
        "days_per_week": 3
        # equipment_available and injuries_or_limitations are optional
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=request)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
def test_workout_recommendation_internal_token_header(
    test_client,
    sample_workout_request,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test X-Internal-Token header is passed correctly."""
    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        token = "test-internal-token-123"

        response = test_client.post(
            "/agent/workout/recommend",
            json=sample_workout_request,
            headers={"X-Internal-Token": token}
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify token was passed to backend client
        call_args = mock_backend_client.get_user_profile.call_args
        assert call_args.args[1] == token


@pytest.mark.unit
def test_workout_recommendation_empty_equipment_list(
    test_client,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test workout recommendation with empty equipment list."""
    request = {
        "user_id": "test-user-123",
        "goal": "general_fitness",
        "fitness_level": "beginner",
        "days_per_week": 3,
        "equipment_available": []  # Empty list
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=request)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
def test_workout_recommendation_with_injuries(
    test_client,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test workout recommendation with injury limitations."""
    request = {
        "user_id": "test-user-123",
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 4,
        "equipment_available": ["barbell", "dumbbell"],
        "injuries_or_limitations": "Lower back pain, avoid deadlifts"
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=request)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
def test_workout_recommendation_all_goals(test_client):
    """Test all valid goal types are accepted."""
    from app.schemas import FitnessGoal

    for goal in FitnessGoal:
        request = {
            "user_id": "test-user-123",
            "goal": goal.value,
            "fitness_level": "intermediate",
            "days_per_week": 3
        }

        # Just test validation, don't need to mock services
        # Invalid because service is not mocked, but validation passes
        response = test_client.post("/agent/workout/recommend", json=request)

        # Should not be 422 (validation error)
        assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.unit
def test_workout_recommendation_all_fitness_levels(test_client):
    """Test all valid fitness levels are accepted."""
    from app.schemas import FitnessLevel

    for level in FitnessLevel:
        request = {
            "user_id": "test-user-123",
            "goal": "general_fitness",
            "fitness_level": level.value,
            "days_per_week": 3
        }

        response = test_client.post("/agent/workout/recommend", json=request)

        # Should not be 422 (validation error)
        assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY
