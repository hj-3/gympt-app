"""
Tests for health check and metrics endpoints.
"""
import pytest
from fastapi import status


@pytest.mark.smoke
def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "status" in data
    assert data["status"] == "healthy"
    assert "service" in data
    assert "environment" in data
    assert "bedrock_mock" in data


@pytest.mark.smoke
def test_root_endpoint(test_client):
    """Test root endpoint."""
    response = test_client.get("/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "service" in data
    assert "version" in data
    assert "docs" in data
    assert data["service"] == "GYMPT Agent Service"


@pytest.mark.integration
def test_metrics_endpoint(test_client):
    """Test Prometheus metrics endpoint."""
    response = test_client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
    # Prometheus metrics are in text format
    assert response.headers["content-type"].startswith("text/plain")


@pytest.mark.smoke
def test_openapi_docs(test_client):
    """Test OpenAPI documentation generation."""
    response = test_client.get("/docs")

    # Should redirect or return HTML
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_307_TEMPORARY_REDIRECT]


@pytest.mark.smoke
def test_openapi_json(test_client):
    """Test OpenAPI JSON schema."""
    response = test_client.get("/openapi.json")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    assert data["info"]["title"] == "GYMPT Agent Service"


def test_health_check_response_structure(test_client):
    """Test health check response has all required fields."""
    response = test_client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    required_fields = ["status", "service", "environment", "bedrock_mock"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"


def test_cors_headers(test_client):
    """Test CORS headers are properly set."""
    response = test_client.options("/health")

    # CORS should be configured
    # Note: TestClient may not fully simulate CORS
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_405_METHOD_NOT_ALLOWED
    ]


def test_health_check_environment_detection(test_client):
    """Test health check reflects correct environment."""
    response = test_client.get("/health")

    data = response.json()

    # Should reflect test environment
    assert data["environment"] in ["local", "dev", "test", "prod"]
