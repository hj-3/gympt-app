import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ["DYNAMODB_TABLE_PREFIX"] = "test"
os.environ["AWS_REGION"] = "ap-northeast-2"
os.environ["S3_BUCKET"] = "test-bucket"

from handler import (
    export_to_csv,
    export_to_json,
    generate_presigned_url,
    get_body_profiles,
    get_workout_sessions,
    lambda_handler,
    upload_to_s3,
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
def sample_sessions():
    return [
        {
            "sessionId": "session-1",
            "exerciseName": "Squat",
            "completedAt": "2024-05-15T10:00:00Z",
            "duration": 300,
            "caloriesBurned": 50,
            "averageScore": 8.5,
            "status": "COMPLETED",
        },
        {
            "sessionId": "session-2",
            "exerciseName": "Pushup",
            "completedAt": "2024-05-16T10:00:00Z",
            "duration": 200,
            "caloriesBurned": 30,
            "averageScore": 9.0,
            "status": "COMPLETED",
        },
    ]


@pytest.fixture
def sample_profiles():
    return [
        {
            "recordedAt": "2024-05-15T00:00:00Z",
            "weight": 70.5,
            "height": 175,
            "bmi": 23.0,
            "bodyFat": 15.2,
            "muscleMass": 55.0,
        }
    ]


def test_get_workout_sessions(mock_dynamodb_table, sample_sessions):
    mock_dynamodb_table.query.return_value = {"Items": sample_sessions}

    sessions = get_workout_sessions(
        "user-123",
        "2024-05-01T00:00:00Z",
        "2024-05-31T23:59:59Z",
    )

    assert len(sessions) == 2
    assert sessions[0]["exerciseName"] == "Squat"


def test_get_body_profiles(mock_dynamodb_table, sample_profiles):
    mock_dynamodb_table.query.return_value = {"Items": sample_profiles}

    profiles = get_body_profiles(
        "user-123",
        "2024-05-01T00:00:00Z",
        "2024-05-31T23:59:59Z",
    )

    assert len(profiles) == 1
    assert profiles[0]["weight"] == 70.5


def test_export_to_csv(sample_sessions, sample_profiles):
    csv_content = export_to_csv(sample_sessions, sample_profiles)

    assert "=== WORKOUT SESSIONS ===" in csv_content
    assert "=== BODY MEASUREMENTS ===" in csv_content
    assert "Squat" in csv_content
    assert "70.5" in csv_content


def test_export_to_json(sample_sessions, sample_profiles):
    json_content = export_to_json(sample_sessions, sample_profiles)

    data = json.loads(json_content)

    assert "workoutSessions" in data
    assert "bodyProfiles" in data
    assert "summary" in data
    assert data["summary"]["totalSessions"] == 2
    assert data["summary"]["totalProfiles"] == 1
    assert data["workoutSessions"][0]["exerciseName"] == "Squat"


def test_upload_to_s3(mock_s3_client):
    content = '{"test": "data"}'

    key = upload_to_s3(content, "user-123", "json")

    assert key.startswith("exports/user-123/")
    assert key.endswith(".json")
    mock_s3_client.put_object.assert_called_once()

    # Check put_object arguments
    call_args = mock_s3_client.put_object.call_args
    assert call_args.kwargs["Bucket"] == "test-bucket"
    assert call_args.kwargs["ContentType"] == "application/json"


def test_upload_to_s3_csv(mock_s3_client):
    content = "col1,col2\nval1,val2"

    key = upload_to_s3(content, "user-123", "csv")

    assert key.endswith(".csv")

    call_args = mock_s3_client.put_object.call_args
    assert call_args.kwargs["ContentType"] == "text/csv"


def test_generate_presigned_url(mock_s3_client):
    mock_s3_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/signed-url"

    url = generate_presigned_url("exports/user-123/export.json")

    assert url == "https://s3.amazonaws.com/signed-url"
    mock_s3_client.generate_presigned_url.assert_called_once()


def test_lambda_handler_json_export(mock_dynamodb_table, mock_s3_client, sample_sessions, sample_profiles):
    # Mock DynamoDB queries
    mock_dynamodb_table.query.side_effect = [
        {"Items": sample_sessions},
        {"Items": sample_profiles},
    ]

    # Mock S3 operations
    mock_s3_client.generate_presigned_url.return_value = "https://presigned-url.com"

    event = {
        "userId": "user-123",
        "format": "json",
        "startDate": "2024-05-01T00:00:00Z",
        "endDate": "2024-05-31T23:59:59Z",
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["userId"] == "user-123"
    assert body["format"] == "json"
    assert body["downloadUrl"] == "https://presigned-url.com"
    assert body["recordCount"]["workoutSessions"] == 2
    assert body["recordCount"]["bodyProfiles"] == 1


def test_lambda_handler_csv_export(mock_dynamodb_table, mock_s3_client, sample_sessions):
    mock_dynamodb_table.query.side_effect = [
        {"Items": sample_sessions},
        {"Items": []},
    ]

    mock_s3_client.generate_presigned_url.return_value = "https://presigned-url.com"

    event = {
        "userId": "user-123",
        "format": "csv",
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["format"] == "csv"
    assert "export.csv" in body["s3Key"]


def test_lambda_handler_sqs_event(mock_dynamodb_table, mock_s3_client, sample_sessions):
    mock_dynamodb_table.query.side_effect = [
        {"Items": sample_sessions},
        {"Items": []},
    ]

    mock_s3_client.generate_presigned_url.return_value = "https://presigned-url.com"

    event = {
        "Records": [
            {
                "body": json.dumps({
                    "userId": "user-123",
                    "format": "json",
                })
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200


def test_lambda_handler_no_data(mock_dynamodb_table):
    mock_dynamodb_table.query.side_effect = [
        {"Items": []},
        {"Items": []},
    ]

    event = {
        "userId": "user-123",
        "format": "json",
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 404
    body = json.loads(result["body"])
    assert "error" in body


def test_lambda_handler_missing_user_id():
    event = {
        "format": "json",
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "error" in body
