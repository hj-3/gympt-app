import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ["DYNAMODB_TABLE_PREFIX"] = "test"
os.environ["AWS_REGION"] = "ap-northeast-2"
os.environ["BACKEND_API_URL"] = "http://test-api"

from handler import (
    calculate_intensity_adjustment,
    generate_recommendation_update,
    get_recent_workout_performance,
    lambda_handler,
)


@pytest.fixture
def mock_dynamodb_table():
    with patch("handler.dynamodb") as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        yield mock_table


def test_get_recent_workout_performance(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {
        "Items": [
            {"averageScore": 8.0, "status": "COMPLETED"},
            {"averageScore": 8.5, "status": "COMPLETED"},
            {"averageScore": 9.0, "status": "COMPLETED"},
        ]
    }

    result = get_recent_workout_performance("user-123", limit=5)

    assert result["averageScore"] == 8.5
    assert result["completionRate"] == 1.0
    assert result["sessions"] == 3


def test_get_recent_workout_performance_with_incomplete(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {
        "Items": [
            {"averageScore": 8.0, "status": "COMPLETED"},
            {"averageScore": 7.0, "status": "INCOMPLETE"},
        ]
    }

    result = get_recent_workout_performance("user-123")

    assert result["completionRate"] == 0.5


def test_get_recent_workout_performance_no_sessions(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {"Items": []}

    result = get_recent_workout_performance("user-123")

    assert result["averageScore"] == 0
    assert result["sessions"] == 0


def test_calculate_intensity_adjustment_increase():
    performance = {
        "averageScore": 9.0,
        "completionRate": 0.95,
        "sessions": 5,
    }

    adjustment = calculate_intensity_adjustment(performance)

    assert adjustment == "INCREASE"


def test_calculate_intensity_adjustment_decrease_low_score():
    performance = {
        "averageScore": 5.5,
        "completionRate": 0.8,
        "sessions": 5,
    }

    adjustment = calculate_intensity_adjustment(performance)

    assert adjustment == "DECREASE"


def test_calculate_intensity_adjustment_decrease_low_completion():
    performance = {
        "averageScore": 7.0,
        "completionRate": 0.4,
        "sessions": 5,
    }

    adjustment = calculate_intensity_adjustment(performance)

    assert adjustment == "DECREASE"


def test_calculate_intensity_adjustment_maintain():
    performance = {
        "averageScore": 7.5,
        "completionRate": 0.8,
        "sessions": 5,
    }

    adjustment = calculate_intensity_adjustment(performance)

    assert adjustment == "MAINTAIN"


def test_calculate_intensity_adjustment_not_enough_data():
    performance = {
        "averageScore": 9.0,
        "completionRate": 1.0,
        "sessions": 2,
    }

    adjustment = calculate_intensity_adjustment(performance)

    assert adjustment == "MAINTAIN"


def test_generate_recommendation_update_increase():
    performance = {
        "averageScore": 9.0,
        "completionRate": 0.95,
        "sessions": 5,
    }

    recommendation = generate_recommendation_update("user-123", "INCREASE", performance)

    assert recommendation["userId"] == "user-123"
    assert recommendation["adjustment"] == "INCREASE"
    assert "Increase weight" in recommendation["recommendations"][0]
    assert recommendation["performanceMetrics"]["averageScore"] == 9.0


def test_generate_recommendation_update_decrease():
    performance = {
        "averageScore": 5.0,
        "completionRate": 0.5,
        "sessions": 5,
    }

    recommendation = generate_recommendation_update("user-123", "DECREASE", performance)

    assert recommendation["adjustment"] == "DECREASE"
    assert "Reduce weight" in recommendation["recommendations"][0]


def test_generate_recommendation_update_maintain():
    performance = {
        "averageScore": 7.5,
        "completionRate": 0.8,
        "sessions": 5,
    }

    recommendation = generate_recommendation_update("user-123", "MAINTAIN", performance)

    assert recommendation["adjustment"] == "MAINTAIN"
    assert "Maintain current intensity" in recommendation["recommendations"][0]


@patch("handler.requests.post")
def test_lambda_handler_success(mock_post, mock_dynamodb_table):
    # Mock DynamoDB query
    mock_dynamodb_table.query.return_value = {
        "Items": [
            {"averageScore": 9.0, "status": "COMPLETED"},
            {"averageScore": 8.5, "status": "COMPLETED"},
            {"averageScore": 9.0, "status": "COMPLETED"},
            {"averageScore": 8.8, "status": "COMPLETED"},
            {"averageScore": 9.2, "status": "COMPLETED"},
        ]
    }

    # Mock API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    event = {
        "Records": [
            {
                "body": json.dumps({
                    "userId": "user-123",
                    "sessionId": "session-abc",
                    "completed": True,
                })
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 1
    assert body["failed"] == 0

    # Verify API was called
    mock_post.assert_called_once()


@patch("handler.requests.post")
def test_lambda_handler_direct_invocation(mock_post, mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {
        "Items": [
            {"averageScore": 7.0, "status": "COMPLETED"},
            {"averageScore": 7.5, "status": "COMPLETED"},
            {"averageScore": 7.2, "status": "COMPLETED"},
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    # Direct invocation (no Records)
    event = {
        "userId": "user-123",
        "sessionId": "session-abc",
        "completed": True,
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 1
