import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ["DYNAMODB_TABLE_PREFIX"] = "test"
os.environ["AWS_REGION"] = "ap-northeast-2"

from handler import (
    get_body_profile,
    get_posture_analysis_result,
    get_recent_workout_sessions,
    get_user_profile,
    lambda_handler,
    save_workout_recommendation,
)


@pytest.fixture
def mock_dynamodb_table():
    with patch("handler.dynamodb") as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        yield mock_table


def test_get_user_profile_success(mock_dynamodb_table):
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "userId": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "USER",
            "status": "ACTIVE",
            "createdAt": "2024-01-01T00:00:00Z",
        }
    }

    result = get_user_profile("user-123")

    assert result["userId"] == "user-123"
    assert result["email"] == "test@example.com"
    assert "error" not in result


def test_get_user_profile_not_found(mock_dynamodb_table):
    mock_dynamodb_table.get_item.return_value = {}

    result = get_user_profile("non-existent")

    assert "error" in result
    assert result["error"] == "User not found"


def test_get_body_profile_success(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {
        "Items": [
            {
                "userId": "user-123",
                "height": 175.0,
                "weight": 70.0,
                "bmi": 22.86,
                "recordedAt": "2024-01-15T00:00:00Z",
            }
        ]
    }

    result = get_body_profile("user-123")

    assert result["userId"] == "user-123"
    assert result["weight"] == 70.0
    assert "error" not in result


def test_get_recent_workout_sessions(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {
        "Items": [
            {
                "sessionId": "session-1",
                "exerciseName": "Squat",
                "duration": 300,
                "averageScore": 8.5,
                "completedAt": "2024-01-15T10:00:00Z",
            },
            {
                "sessionId": "session-2",
                "exerciseName": "Pushup",
                "duration": 180,
                "averageScore": 9.0,
                "completedAt": "2024-01-14T10:00:00Z",
            },
        ]
    }

    result = get_recent_workout_sessions("user-123", limit=10)

    assert result["userId"] == "user-123"
    assert result["count"] == 2
    assert len(result["sessions"]) == 2
    assert result["sessions"][0]["exerciseName"] == "Squat"


def test_save_workout_recommendation(mock_dynamodb_table):
    recommendation = {
        "workoutPlan": "Strength Training",
        "exercises": ["Squat", "Bench Press", "Deadlift"],
        "duration": 45,
        "intensity": "MODERATE",
    }

    result = save_workout_recommendation("user-123", recommendation)

    assert result["success"] is True
    assert result["userId"] == "user-123"
    assert "recommendationId" in result
    mock_dynamodb_table.put_item.assert_called_once()


def test_get_posture_analysis_result(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {
        "Items": [
            {
                "sessionId": "session-1",
                "score": 8.0,
                "issues": [
                    {"type": "knee_valgus", "severity": "medium"}
                ],
            },
            {
                "sessionId": "session-1",
                "score": 7.5,
                "issues": [
                    {"type": "depth", "severity": "low"}
                ],
            },
        ]
    }

    result = get_posture_analysis_result("session-1")

    assert result["sessionId"] == "session-1"
    assert result["eventCount"] == 2
    assert result["averageScore"] == 7.75
    assert result["totalIssues"] == 2


def test_lambda_handler_get_user_profile(mock_dynamodb_table):
    mock_dynamodb_table.get_item.return_value = {
        "Item": {
            "userId": "user-123",
            "email": "test@example.com",
            "name": "Test User",
        }
    }

    event = {
        "actionGroup": "WorkoutActions",
        "function": "getUserProfile",
        "parameters": [{"name": "userId", "value": "user-123"}],
    }

    result = lambda_handler(event, None)

    assert result["messageVersion"] == "1.0"
    assert result["response"]["function"] == "getUserProfile"
    response_body = json.loads(
        result["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    )
    assert response_body["userId"] == "user-123"


def test_lambda_handler_unknown_function():
    event = {
        "actionGroup": "WorkoutActions",
        "function": "unknownFunction",
        "parameters": [],
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 400
    assert "error" in json.loads(result["body"])
