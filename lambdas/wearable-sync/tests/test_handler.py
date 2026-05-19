import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ["DYNAMODB_TABLE_PREFIX"] = "test"
os.environ["AWS_REGION"] = "ap-northeast-2"

from handler import (
    calculate_daily_aggregates,
    lambda_handler,
    normalize_metrics,
    save_wearable_event,
    validate_wearable_data,
)


def test_validate_wearable_data_success():
    data = {
        "userId": "user-123",
        "deviceType": "apple_watch",
        "timestamp": "2024-05-18T14:30:00Z",
        "metrics": {"heartRate": 75},
    }

    assert validate_wearable_data(data) is True


def test_validate_wearable_data_missing_field():
    data = {
        "userId": "user-123",
        "deviceType": "apple_watch",
        # Missing timestamp
        "metrics": {"heartRate": 75},
    }

    assert validate_wearable_data(data) is False


def test_validate_wearable_data_invalid_metrics():
    data = {
        "userId": "user-123",
        "deviceType": "apple_watch",
        "timestamp": "2024-05-18T14:30:00Z",
        "metrics": "not a dict",
    }

    assert validate_wearable_data(data) is False


def test_normalize_metrics_apple_watch():
    metrics = {
        "heartRate": 75,
        "steps": 1000,
        "calories": 50,
        "activeMinutes": 10,
    }

    normalized = normalize_metrics(metrics, "apple_watch")

    assert normalized["heartRate"] == 75
    assert normalized["steps"] == 1000
    assert normalized["calories"] == 50
    assert normalized["activeMinutes"] == 10


def test_normalize_metrics_fitbit():
    metrics = {
        "heart_rate": 75,
        "steps": 1000,
        "calories_burned": 50,
        "active_minutes": 10,
        "distance_meters": 800,
    }

    normalized = normalize_metrics(metrics, "fitbit")

    assert normalized["heartRate"] == 75
    assert normalized["steps"] == 1000
    assert normalized["calories"] == 50
    assert normalized["activeMinutes"] == 10
    assert normalized["distance"] == 0.8  # Converted from meters to km


def test_normalize_metrics_garmin():
    metrics = {
        "hr": 75,
        "step_count": 1000,
        "kcal": 50,
        "active_time_minutes": 10,
    }

    normalized = normalize_metrics(metrics, "garmin")

    assert normalized["heartRate"] == 75
    assert normalized["steps"] == 1000
    assert normalized["calories"] == 50
    assert normalized["activeMinutes"] == 10


def test_normalize_metrics_with_sleep():
    metrics = {
        "heartRate": 60,
        "sleepMinutes": 480,
    }

    normalized = normalize_metrics(metrics, "apple_watch")

    assert normalized["heartRate"] == 60
    assert normalized["sleepMinutes"] == 480


@pytest.fixture
def mock_dynamodb_table():
    with patch("handler.dynamodb") as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        yield mock_table


def test_save_wearable_event(mock_dynamodb_table):
    event_data = {
        "userId": "user-123",
        "deviceType": "apple_watch",
        "deviceId": "watch-001",
        "timestamp": "2024-05-18T14:30:00Z",
        "metrics": {"heartRate": 75},
        "normalizedMetrics": {"heartRate": 75},
    }

    result = save_wearable_event(event_data)

    assert result is True
    mock_dynamodb_table.put_item.assert_called_once()


def test_calculate_daily_aggregates(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {
        "Items": [
            {
                "metrics": {
                    "heartRate": 70,
                    "steps": 500,
                    "calories": 25,
                    "activeMinutes": 5,
                }
            },
            {
                "metrics": {
                    "heartRate": 80,
                    "steps": 500,
                    "calories": 25,
                    "activeMinutes": 5,
                }
            },
        ]
    }

    result = calculate_daily_aggregates("user-123", "2024-05-18")

    assert result["date"] == "2024-05-18"
    assert result["totalEvents"] == 2
    assert result["totalSteps"] == 1000
    assert result["totalCalories"] == 50
    assert result["totalActiveMinutes"] == 10
    assert result["averageHeartRate"] == 75.0


def test_calculate_daily_aggregates_no_events(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {"Items": []}

    result = calculate_daily_aggregates("user-123", "2024-05-18")

    assert result["date"] == "2024-05-18"
    assert result["totalEvents"] == 0


def test_lambda_handler_success(mock_dynamodb_table):
    # Mock query for calculate_daily_aggregates
    mock_dynamodb_table.query.return_value = {"Items": []}

    event = {
        "Records": [
            {
                "messageId": "msg-1",
                "body": json.dumps({
                    "userId": "user-123",
                    "deviceType": "apple_watch",
                    "deviceId": "watch-001",
                    "timestamp": "2024-05-18T14:30:00Z",
                    "metrics": {
                        "heartRate": 75,
                        "steps": 1000,
                    },
                }),
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 1
    assert body["failed"] == 0


def test_lambda_handler_invalid_data(mock_dynamodb_table):
    event = {
        "Records": [
            {
                "messageId": "msg-1",
                "body": json.dumps({
                    "userId": "user-123",
                    # Missing required fields
                    "metrics": {"heartRate": 75},
                }),
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 0
    assert body["failed"] == 1


def test_lambda_handler_multiple_devices(mock_dynamodb_table):
    mock_dynamodb_table.query.return_value = {"Items": []}

    event = {
        "Records": [
            {
                "body": json.dumps({
                    "userId": "user-1",
                    "deviceType": "apple_watch",
                    "timestamp": "2024-05-18T14:30:00Z",
                    "metrics": {"heartRate": 75},
                }),
            },
            {
                "body": json.dumps({
                    "userId": "user-2",
                    "deviceType": "fitbit",
                    "timestamp": "2024-05-18T14:30:00Z",
                    "metrics": {"heart_rate": 80},
                }),
            },
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 2
