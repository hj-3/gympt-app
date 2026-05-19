import json
import os
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

os.environ["AWS_REGION"] = "ap-northeast-2"
os.environ["S3_BUCKET"] = "test-bucket"

from handler import (
    generate_mock_thumbnail,
    generate_thumbnail_from_video,
    lambda_handler,
    process_s3_event,
    process_sqs_message,
    save_thumbnail_to_s3,
)


def test_generate_mock_thumbnail():
    thumbnail = generate_mock_thumbnail(320, 180)

    assert isinstance(thumbnail, BytesIO)
    assert thumbnail.tell() == 0  # Cursor at beginning

    # Verify it's a valid JPEG
    img = Image.open(thumbnail)
    assert img.format == "JPEG"
    assert img.size == (320, 180)


def test_generate_thumbnail_from_video():
    thumbnail = generate_thumbnail_from_video("test-bucket", "videos/test.mp4")

    assert isinstance(thumbnail, BytesIO)

    # Verify it's a valid image
    img = Image.open(thumbnail)
    assert img.format == "JPEG"


@pytest.fixture
def mock_s3_client():
    with patch("handler.s3_client") as mock_s3:
        yield mock_s3


def test_save_thumbnail_to_s3(mock_s3_client):
    thumbnail = generate_mock_thumbnail(320, 180)
    original_key = "videos/user-123/session-abc/workout.mp4"

    result_key = save_thumbnail_to_s3(thumbnail, original_key)

    assert result_key == "thumbnails/user-123/session-abc/workout.jpg"
    mock_s3_client.put_object.assert_called_once()

    # Check put_object arguments
    call_args = mock_s3_client.put_object.call_args
    assert call_args.kwargs["Bucket"] == "test-bucket"
    assert call_args.kwargs["Key"] == "thumbnails/user-123/session-abc/workout.jpg"
    assert call_args.kwargs["ContentType"] == "image/jpeg"


def test_save_thumbnail_to_s3_no_videos_prefix(mock_s3_client):
    thumbnail = generate_mock_thumbnail(320, 180)
    original_key = "user-123/workout.mp4"

    result_key = save_thumbnail_to_s3(thumbnail, original_key)

    assert result_key == "thumbnails/user-123/workout.jpg"


def test_process_s3_event(mock_s3_client):
    event = {
        "s3": {
            "bucket": {"name": "test-bucket"},
            "object": {"key": "videos/user-123/workout.mp4"},
        }
    }

    result = process_s3_event(event)

    assert result["originalKey"] == "videos/user-123/workout.mp4"
    assert result["thumbnailKey"] == "thumbnails/user-123/workout.jpg"
    assert result["bucket"] == "test-bucket"


def test_process_sqs_message(mock_s3_client):
    message = {
        "sessionId": "session-abc",
        "videoKey": "videos/user-123/workout.mp4",
        "bucket": "test-bucket",
    }

    result = process_sqs_message(message)

    assert result["sessionId"] == "session-abc"
    assert result["originalKey"] == "videos/user-123/workout.mp4"
    assert result["thumbnailKey"] == "thumbnails/user-123/workout.jpg"


def test_lambda_handler_s3_event(mock_s3_client):
    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "videos/user-123/workout.mp4"},
                }
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 1
    assert len(body["results"]) == 1


def test_lambda_handler_sqs_event(mock_s3_client):
    event = {
        "Records": [
            {
                "body": json.dumps({
                    "sessionId": "session-abc",
                    "videoKey": "videos/user-123/workout.mp4",
                })
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 1


def test_lambda_handler_multiple_records(mock_s3_client):
    event = {
        "Records": [
            {
                "body": json.dumps({
                    "sessionId": "session-1",
                    "videoKey": "videos/user-1/workout.mp4",
                })
            },
            {
                "body": json.dumps({
                    "sessionId": "session-2",
                    "videoKey": "videos/user-2/workout.mp4",
                })
            },
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 2
