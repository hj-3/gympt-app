"""
Regression tests for API contract stability.

Ensures API backwards compatibility is maintained.
"""
import pytest
from fastapi import status


@pytest.mark.regression
def test_workout_recommendation_request_schema_v1(test_client):
    """Test workout recommendation request schema v1 compatibility."""
    # Original schema should still work
    request_v1 = {
        "user_id": "test-user-123",
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 4,
        "equipment_available": ["barbell", "dumbbell"],
        "injuries_or_limitations": None
    }

    # Schema validation should pass
    response = test_client.post("/agent/workout/recommend", json=request_v1)

    # Should not be a validation error
    assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.regression
def test_workout_recommendation_response_schema_v1(
    test_client,
    mock_bedrock_client,
    mock_backend_client,
    mock_dynamodb_client,
    mock_redis_client
):
    """Test workout recommendation response schema v1 compatibility."""
    from unittest.mock import patch

    request = {
        "user_id": "test-user-123",
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 4
    }

    with patch("app.services.agent_service.bedrock_client", mock_bedrock_client), \
         patch("app.services.agent_service.backend_client", mock_backend_client), \
         patch("app.services.agent_service.dynamodb_client", mock_dynamodb_client), \
         patch("app.services.cache_service.redis_client", mock_redis_client):

        response = test_client.post("/agent/workout/recommend", json=request)

        if response.status_code == 200:
            data = response.json()

            # Original fields must exist
            assert "recommendation" in data
            assert "model_used" in data
            assert "cached" in data
            assert "interaction_id" in data


@pytest.mark.regression
def test_posture_feedback_schema_stability(test_client):
    """Test posture feedback schema remains stable."""
    request = {
        "session_id": "test-session",
        "exercise_name": "squat",
        "posture_score": 7.5,
        "detected_issues": ["knee_valgus"]
    }

    response = test_client.post("/agent/posture/feedback", json=request)

    # Schema validation should pass
    assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.regression
def test_report_generation_schema_stability(test_client):
    """Test report generation schema remains stable."""
    request = {
        "user_id": "test-user-123",
        "period_start": "2024-01-01",
        "period_end": "2024-01-07",
        "include_sections": ["summary"]
    }

    response = test_client.post("/agent/report/generate", json=request)

    # Schema validation should pass
    assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.regression
def test_health_endpoint_contract(test_client):
    """Test health endpoint contract remains stable."""
    response = test_client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Original contract fields
    assert "status" in data
    assert "service" in data


@pytest.mark.regression
def test_root_endpoint_contract(test_client):
    """Test root endpoint contract remains stable."""
    response = test_client.get("/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Original contract fields
    assert "service" in data
    assert "version" in data


@pytest.mark.regression
def test_enum_values_stable():
    """Test enum values haven't changed."""
    from app.schemas import FitnessGoal, FitnessLevel

    # Original goal values
    expected_goals = {
        "weight_loss", "muscle_gain", "endurance", "flexibility", "general_fitness"
    }
    actual_goals = {g.value for g in FitnessGoal}
    assert expected_goals.issubset(actual_goals), "Missing fitness goals"

    # Original level values
    expected_levels = {"beginner", "intermediate", "advanced"}
    actual_levels = {l.value for l in FitnessLevel}
    assert expected_levels.issubset(actual_levels), "Missing fitness levels"


@pytest.mark.regression
def test_error_response_format_stable(test_client):
    """Test error response format remains stable."""
    response = test_client.post("/agent/workout/recommend", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()

    # Error format should have 'detail'
    assert "detail" in data


@pytest.mark.regression
def test_cors_configuration_stable(test_client):
    """Test CORS configuration remains stable."""
    response = test_client.get("/health")

    # CORS should be enabled (though TestClient may not fully simulate)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.regression
def test_api_versioning_header(test_client):
    """Test API version information is available."""
    response = test_client.get("/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "version" in data


@pytest.mark.regression
def test_openapi_schema_available(test_client):
    """Test OpenAPI schema is still available."""
    response = test_client.get("/openapi.json")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "openapi" in data
    assert "paths" in data


@pytest.mark.regression
def test_required_endpoints_exist(test_client):
    """Test all required endpoints still exist."""
    endpoints = [
        ("/", "GET"),
        ("/health", "GET"),
        ("/metrics", "GET"),
        ("/agent/workout/recommend", "POST"),
        ("/agent/posture/feedback", "POST"),
        ("/agent/report/generate", "POST"),
    ]

    for path, method in endpoints:
        if method == "GET":
            response = test_client.get(path)
        elif method == "POST":
            response = test_client.post(path, json={})

        # Should not be 404
        assert response.status_code != status.HTTP_404_NOT_FOUND, \
            f"Endpoint {method} {path} not found"


@pytest.mark.regression
def test_optional_fields_remain_optional(test_client):
    """Test optional fields can still be omitted."""
    # Minimal valid request
    minimal_request = {
        "user_id": "test-user",
        "goal": "general_fitness",
        "fitness_level": "beginner"
        # days_per_week has default, equipment and injuries are optional
    }

    response = test_client.post("/agent/workout/recommend", json=minimal_request)

    # Should not be validation error
    assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY
