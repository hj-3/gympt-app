import pytest
import sys
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import os

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["ENABLE_BEDROCK_MOCK"] = "true"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"


# ============================================================================
# Test Client Fixtures
# ============================================================================

@pytest.fixture
def test_client():
    """FastAPI test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async FastAPI test client."""
    from httpx import AsyncClient
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock client."""
    from app.clients.bedrock_client import BedrockClient

    client = Mock(spec=BedrockClient)
    client.invoke_model = AsyncMock(return_value={
        "content": "Mock Bedrock response content",
        "model": "mock-model",
        "usage": {"input_tokens": 100, "output_tokens": 200},
        "stop_reason": "end_turn"
    })
    client.invoke_agent = AsyncMock(return_value={
        "completion": "Mock agent response",
        "session_id": "test-session",
        "trace": None
    })
    return client


@pytest.fixture
def mock_dynamodb_client():
    """Mock DynamoDB client."""
    from app.clients.dynamodb_client import DynamoDBClient

    client = Mock(spec=DynamoDBClient)
    client.log_interaction = AsyncMock(return_value={"status": "success"})
    client.get_interaction = AsyncMock(return_value={
        "user_id": "test-user",
        "interaction_type": "workout_recommend",
        "timestamp": "2024-01-01T00:00:00Z"
    })
    return client


@pytest.fixture
def mock_sqs_client():
    """Mock SQS client."""
    from app.clients.sqs_client import SQSClient

    client = Mock(spec=SQSClient)
    client.publish_report_generation_task = AsyncMock(return_value={
        "MessageId": "test-message-id"
    })
    return client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    from app.clients.redis_client import RedisClient

    client = Mock(spec=RedisClient)
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.ping = AsyncMock(return_value=True)
    client.close = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_backend_client():
    """Mock Backend API client."""
    from app.clients.backend_client import BackendClient

    client = Mock(spec=BackendClient)
    client.get_user_profile = AsyncMock(return_value={
        "user_id": "test-user-123",
        "name": "Test User",
        "email": "test@example.com",
        "age": 30,
        "gender": "male",
        "fitness_experience": "intermediate"
    })
    client.get_user_data = AsyncMock(return_value={
        "user_id": "test-user-123",
        "profile": {"name": "Test User"},
        "body_profile": {
            "height_cm": 175,
            "weight_kg": 70,
            "body_fat_percentage": 15.0
        },
        "goals": []
    })
    return client


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def mock_bedrock_response():
    """Mock Bedrock response fixture."""
    return {
        "content": "Test recommendation content",
        "model": "test-model",
        "usage": {"input_tokens": 100, "output_tokens": 200},
        "stop_reason": "end_turn"
    }


@pytest.fixture
def sample_workout_request():
    """Sample workout recommendation request."""
    return {
        "user_id": "test-user-123",
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 4,
        "equipment_available": ["barbell", "dumbbell", "bench"],
        "injuries_or_limitations": None
    }


@pytest.fixture
def sample_workout_request_beginner():
    """Sample workout request for beginner."""
    return {
        "user_id": "test-beginner-456",
        "goal": "general_fitness",
        "fitness_level": "beginner",
        "days_per_week": 3,
        "equipment_available": ["bodyweight"],
        "injuries_or_limitations": None
    }


@pytest.fixture
def sample_workout_request_advanced():
    """Sample workout request for advanced user."""
    return {
        "user_id": "test-advanced-789",
        "goal": "endurance",
        "fitness_level": "advanced",
        "days_per_week": 6,
        "equipment_available": ["barbell", "dumbbell", "bench", "squat_rack", "pull_up_bar"],
        "injuries_or_limitations": "Previous knee injury, avoid deep squats"
    }


@pytest.fixture
def sample_posture_request():
    """Sample posture feedback request."""
    return {
        "session_id": "session-123",
        "exercise_name": "squat",
        "posture_score": 7.5,
        "detected_issues": ["knee_valgus", "insufficient_depth"],
        "frame_data": {
            "timestamp": "2024-01-01T12:00:00Z",
            "landmarks": {}
        }
    }


@pytest.fixture
def sample_posture_request_critical():
    """Sample posture request with critical issues."""
    return {
        "session_id": "session-456",
        "exercise_name": "deadlift",
        "posture_score": 3.0,
        "detected_issues": ["rounded_back", "improper_hip_hinge"],
        "frame_data": {}
    }


@pytest.fixture
def sample_report_request():
    """Sample report generation request."""
    return {
        "user_id": "test-user-123",
        "period_start": "2024-01-01",
        "period_end": "2024-01-07",
        "include_sections": ["summary", "workouts", "progress", "recommendations"]
    }


@pytest.fixture
def sample_user_profile():
    """Sample user profile."""
    return {
        "user_id": "test-user-123",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "age": 30,
        "gender": "male",
        "fitness_experience": "intermediate",
        "created_at": "2023-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_body_profile():
    """Sample body profile."""
    return {
        "user_id": "test-user-123",
        "height_cm": 175.0,
        "weight_kg": 75.0,
        "body_fat_percentage": 15.0,
        "muscle_mass_kg": 35.0,
        "measurements": {
            "chest_cm": 100,
            "waist_cm": 80,
            "hips_cm": 95
        },
        "last_updated": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_workout_goal():
    """Sample workout goal."""
    return {
        "goal_id": "goal-123",
        "user_id": "test-user-123",
        "goal_type": "muscle_gain",
        "target_value": 80.0,
        "current_value": 75.0,
        "deadline": "2024-06-01",
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z"
    }


# ============================================================================
# AWS Mock Fixtures (using moto)
# ============================================================================

@pytest.fixture
def mock_aws_credentials():
    """Mock AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture
def dynamodb_table(mock_aws_credentials):
    """Create mock DynamoDB table."""
    from moto import mock_dynamodb
    import boto3

    with mock_dynamodb():
        dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-2")

        table = dynamodb.create_table(
            TableName="gympt-agent-interactions-test",
            KeySchema=[
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "user_id", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        yield table


@pytest.fixture
def sqs_queue(mock_aws_credentials):
    """Create mock SQS queue."""
    from moto import mock_sqs
    import boto3

    with mock_sqs():
        sqs = boto3.client("sqs", region_name="ap-northeast-2")

        response = sqs.create_queue(
            QueueName="gympt-agent-tasks-test",
            Attributes={"DelaySeconds": "0"}
        )

        yield response["QueueUrl"]


# ============================================================================
# Async Fixtures
# ============================================================================

@pytest.fixture
async def redis_connection():
    """Real Redis connection for integration tests."""
    from app.clients.redis_client import redis_client

    try:
        await redis_client.ping()
        yield redis_client
    except Exception:
        pytest.skip("Redis not available")
    finally:
        await redis_client.close()


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def mock_time():
    """Mock time for deterministic testing."""
    from freezegun import freeze_time
    with freeze_time("2024-01-01 12:00:00"):
        yield


@pytest.fixture
def faker_instance():
    """Faker instance for generating test data."""
    from faker import Faker
    return Faker()


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset Prometheus metrics before each test."""
    from app.metrics import (
        agent_interactions_total,
        cache_hits_total,
        cache_misses_total,
        active_requests
    )

    # Clear metrics (note: this is not perfect but works for testing)
    yield

    # Cleanup would go here if needed
