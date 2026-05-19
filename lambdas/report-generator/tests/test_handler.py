import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ["DYNAMODB_TABLE_PREFIX"] = "test"
os.environ["AWS_REGION"] = "ap-northeast-2"
os.environ["S3_BUCKET"] = "test-bucket"
os.environ["ENABLE_BEDROCK_MOCK"] = "true"

from handler import (
    calculate_metrics,
    generate_report_with_bedrock,
    get_posture_events,
    get_workout_sessions,
    lambda_handler,
)


@pytest.fixture
def mock_dynamodb_table():
    with patch("handler.dynamodb") as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_s3_client():
    with patch("handler.s3_client") as mock_s3:
        yield mock_s3


@pytest.fixture
def mock_sqs_client():
    with patch("handler.sqs_client") as mock_sqs:
        yield mock_sqs


def test_get_workout_sessions(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {
        "Items": [
            {
                "sessionId": "session-1",
                "userId": "user-123",
                "exerciseName": "Squat",
                "duration": 300,
                "caloriesBurned": 50,
                "completedAt": "2024-05-15T10:00:00Z",
            },
            {
                "sessionId": "session-2",
                "userId": "user-123",
                "exerciseName": "Pushup",
                "duration": 200,
                "caloriesBurned": 30,
                "completedAt": "2024-05-16T10:00:00Z",
            },
        ]
    }

    sessions = get_workout_sessions(
        "user-123",
        "2024-05-11T00:00:00Z",
        "2024-05-18T00:00:00Z",
    )

    assert len(sessions) == 2
    assert sessions[0]["exerciseName"] == "Squat"


def test_get_posture_events(mock_dynamodb_table):
    mock_dynamodb_table.query.side_effect = [
        {
            "Items": [
                {
                    "sessionId": "session-1",
                    "score": 8.0,
                    "issues": [{"type": "knee_valgus", "severity": "medium"}],
                }
            ]
        },
        {
            "Items": [
                {
                    "sessionId": "session-2",
                    "score": 9.0,
                    "issues": [],
                }
            ]
        },
    ]

    events = get_posture_events(["session-1", "session-2"])

    assert "session-1" in events
    assert "session-2" in events
    assert len(events["session-1"]) == 1
    assert events["session-1"][0]["score"] == 8.0


def test_calculate_metrics():
    sessions = [
        {
            "sessionId": "session-1",
            "exerciseName": "Squat",
            "duration": 300,
            "caloriesBurned": 50,
        },
        {
            "sessionId": "session-2",
            "exerciseName": "Pushup",
            "duration": 200,
            "caloriesBurned": 30,
        },
    ]

    posture_events = {
        "session-1": [
            {
                "score": 8.0,
                "issues": [{"type": "knee_valgus", "severity": "medium"}],
            }
        ],
        "session-2": [
            {
                "score": 9.0,
                "issues": [{"type": "elbow_flare", "severity": "low"}],
            }
        ],
    }

    metrics = calculate_metrics(sessions, posture_events)

    assert metrics["totalSessions"] == 2
    assert metrics["totalDuration"] == 500
    assert metrics["totalCalories"] == 80
    assert metrics["averageScore"] == 8.5
    assert "Squat" in metrics["exerciseBreakdown"]
    assert len(metrics["commonIssues"]) > 0


def test_calculate_metrics_empty():
    metrics = calculate_metrics([], {})

    assert metrics["totalSessions"] == 0
    assert metrics["totalDuration"] == 0
    assert metrics["averageScore"] == 0


def test_generate_report_with_bedrock_mock():
    metrics = {
        "totalSessions": 5,
        "totalDuration": 1500,
        "totalCalories": 250,
        "averageScore": 8.5,
        "commonIssues": [("knee_valgus", 3), ("depth", 2)],
    }

    insights = generate_report_with_bedrock("user-123", metrics, "weekly")

    assert "Performance Summary" in insights
    assert "Recommendations" in insights
    assert isinstance(insights, str)
    assert len(insights) > 0


def test_lambda_handler_success(mock_dynamodb_table, mock_s3_client, mock_sqs_client):
    # Mock DynamoDB responses
    mock_dynamodb_table.query.side_effect = [
        {
            "Items": [
                {
                    "sessionId": "session-1",
                    "userId": "user-123",
                    "exerciseName": "Squat",
                    "duration": 300,
                    "caloriesBurned": 50,
                }
            ]
        },
        {
            "Items": [
                {
                    "score": 8.0,
                    "issues": [{"type": "knee_valgus", "severity": "medium"}],
                }
            ]
        },
    ]

    event = {
        "Records": [
            {
                "messageId": "msg-1",
                "body": json.dumps({
                    "userId": "user-123",
                    "period": "weekly",
                    "requestedAt": "2024-05-18T10:00:00Z",
                }),
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    mock_s3_client.put_object.assert_called_once()


def test_lambda_handler_no_sessions(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {"Items": []}

    event = {
        "Records": [
            {
                "messageId": "msg-1",
                "body": json.dumps({
                    "userId": "user-123",
                    "period": "weekly",
                    "requestedAt": "2024-05-18T10:00:00Z",
                }),
            }
        ]
    }

    result = lambda_handler(event, None)

    # Should still return success even with no sessions
    assert result["statusCode"] == 200
