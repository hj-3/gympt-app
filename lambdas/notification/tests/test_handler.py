import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ["AWS_REGION"] = "ap-northeast-2"
os.environ["ENABLE_SLACK"] = "false"
os.environ["ENABLE_EMAIL"] = "false"
os.environ["ENABLE_PUSH"] = "false"

from handler import (
    lambda_handler,
    log_notification,
    send_email_notification,
    send_push_notification,
    send_slack_notification,
)


def test_log_notification(caplog):
    message = {
        "type": "REPORT_READY",
        "userId": "user-123",
        "reportUrl": "s3://bucket/report.json",
    }

    log_notification(message)

    assert "NOTIFICATION: REPORT_READY" in caplog.text
    assert "user-123" in caplog.text


@patch("handler.requests.post")
def test_send_slack_notification_disabled(mock_post):
    message = {"type": "REPORT_READY", "userId": "user-123"}

    result = send_slack_notification(message)

    assert result is False
    mock_post.assert_not_called()


@patch("handler.ENABLE_SLACK", True)
@patch("handler.SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")
@patch("handler.requests.post")
def test_send_slack_notification_enabled(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    message = {"type": "REPORT_READY", "userId": "user-123"}

    result = send_slack_notification(message)

    assert result is True
    mock_post.assert_called_once()

    # Check payload structure
    call_args = mock_post.call_args
    payload = call_args.kwargs["json"]
    assert "attachments" in payload


def test_send_email_notification_disabled():
    message = {"type": "REPORT_READY", "userId": "user-123"}

    result = send_email_notification(message)

    assert result is False


@patch("handler.ENABLE_EMAIL", True)
@patch("handler.SNS_TOPIC_ARN", "arn:aws:sns:ap-northeast-2:123:topic")
@patch("handler.sns_client")
def test_send_email_notification_enabled(mock_sns):
    message = {
        "type": "REPORT_READY",
        "userId": "user-123",
        "reportUrl": "s3://bucket/report.json",
    }

    result = send_email_notification(message)

    assert result is True
    mock_sns.publish.assert_called_once()

    # Check SNS publish arguments
    call_args = mock_sns.publish.call_args
    assert call_args.kwargs["Subject"] == "Your Workout Report is Ready"
    assert "s3://bucket/report.json" in call_args.kwargs["Message"]


def test_send_push_notification_disabled():
    message = {"type": "WORKOUT_COMPLETED", "userId": "user-123"}

    result = send_push_notification(message)

    assert result is False


@patch("handler.ENABLE_PUSH", True)
def test_send_push_notification_enabled():
    message = {"type": "WORKOUT_COMPLETED", "userId": "user-123"}

    result = send_push_notification(message)

    # Mock implementation always returns True
    assert result is True


def test_lambda_handler_all_channels_disabled():
    event = {
        "Records": [
            {
                "messageId": "msg-1",
                "body": json.dumps({
                    "type": "REPORT_READY",
                    "userId": "user-123",
                }),
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    # With all channels disabled, still counts as processed (logs only)
    assert body["processed"] == 1
    assert body["failed"] == 0


@patch("handler.ENABLE_SLACK", True)
@patch("handler.SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")
@patch("handler.requests.post")
def test_lambda_handler_slack_enabled(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    event = {
        "Records": [
            {
                "body": json.dumps({
                    "type": "WORKOUT_COMPLETED",
                    "userId": "user-123",
                    "sessionId": "session-abc",
                }),
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 1

    mock_post.assert_called_once()


def test_lambda_handler_multiple_notifications():
    event = {
        "Records": [
            {
                "body": json.dumps({
                    "type": "REPORT_READY",
                    "userId": "user-1",
                }),
            },
            {
                "body": json.dumps({
                    "type": "WORKOUT_COMPLETED",
                    "userId": "user-2",
                }),
            },
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 2


def test_lambda_handler_invalid_message():
    event = {
        "Records": [
            {
                "body": "invalid json",
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["failed"] == 1
