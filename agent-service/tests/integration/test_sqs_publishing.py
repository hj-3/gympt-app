import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.clients.sqs_client import sqs_client


@pytest.mark.asyncio
class TestSQSPublishing:
    """Integration tests for SQS message publishing."""

    @patch("aioboto3.Session")
    async def test_publish_task_success(self, mock_session_class):
        """Test successful task publishing to SQS."""
        # Mock SQS client
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={
            "MessageId": "msg-123",
            "MD5OfMessageBody": "abc123"
        })
        mock_sqs.__aenter__.return_value = mock_sqs
        mock_sqs.__aexit__.return_value = AsyncMock()

        # Mock session
        mock_session = MagicMock()
        mock_session.client.return_value = mock_sqs
        mock_session_class.return_value = mock_session

        # Test message
        message_body = {
            "task_type": "posture_analysis",
            "user_id": "user123",
            "session_id": "session456"
        }
        message_attributes = {
            "TaskType": "posture_analysis",
            "Priority": "high"
        }

        # Execute
        result = await sqs_client.publish_task(
            queue_name="posture-analysis-queue",
            message_body=message_body,
            message_attributes=message_attributes
        )

        # Assertions
        assert result == "msg-123"
        mock_sqs.send_message.assert_called_once()

        # Verify message structure
        call_args = mock_sqs.send_message.call_args
        assert "QueueUrl" in call_args.kwargs
        assert "MessageBody" in call_args.kwargs
        assert "MessageAttributes" in call_args.kwargs

    @patch("aioboto3.Session")
    async def test_publish_posture_analysis_task(self, mock_session_class):
        """Test publishing posture analysis task."""
        # Mock SQS client
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={
            "MessageId": "msg-posture-123"
        })
        mock_sqs.__aenter__.return_value = mock_sqs
        mock_sqs.__aexit__.return_value = AsyncMock()

        # Mock session
        mock_session = MagicMock()
        mock_session.client.return_value = mock_sqs
        mock_session_class.return_value = mock_session

        # Test data
        frame_data = {
            "landmarks": [{"x": 0.5, "y": 0.5, "z": 0.0}],
            "timestamp": "2024-01-15T10:00:00"
        }

        # Execute
        result = await sqs_client.publish_posture_analysis_task(
            session_id="session456",
            user_id="user123",
            exercise_name="Squat",
            frame_data=frame_data
        )

        # Assertions
        assert result == "msg-posture-123"
        mock_sqs.send_message.assert_called_once()

    @patch("aioboto3.Session")
    async def test_publish_report_generation_task(self, mock_session_class):
        """Test publishing report generation task."""
        # Mock SQS client
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={
            "MessageId": "msg-report-456"
        })
        mock_sqs.__aenter__.return_value = mock_sqs
        mock_sqs.__aexit__.return_value = AsyncMock()

        # Mock session
        mock_session = MagicMock()
        mock_session.client.return_value = mock_sqs
        mock_session_class.return_value = mock_session

        # Test data
        report_data = {
            "summary": "Great progress this month",
            "workouts_completed": 12,
            "insights": ["Consistency improved", "Strength gains"]
        }

        # Execute
        result = await sqs_client.publish_report_generation_task(
            user_id="user123",
            report_id="report-789",
            period_start="2024-01-01",
            period_end="2024-01-31",
            report_data=report_data
        )

        # Assertions
        assert result == "msg-report-456"
        mock_sqs.send_message.assert_called_once()

        # Verify message structure
        call_args = mock_sqs.send_message.call_args
        message_body = call_args.kwargs["MessageBody"]
        assert "user123" in message_body
        assert "report-789" in message_body

    @patch("aioboto3.Session")
    async def test_publish_task_handles_failure(self, mock_session_class):
        """Test graceful handling of SQS publish failure."""
        # Mock SQS client that raises exception
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(
            side_effect=Exception("SQS service unavailable")
        )
        mock_sqs.__aenter__.return_value = mock_sqs
        mock_sqs.__aexit__.return_value = AsyncMock()

        # Mock session
        mock_session = MagicMock()
        mock_session.client.return_value = mock_sqs
        mock_session_class.return_value = mock_session

        # Execute
        result = await sqs_client.publish_task(
            queue_name="test-queue",
            message_body={"test": "data"},
            message_attributes=None
        )

        # Should return None but not raise exception (graceful degradation)
        assert result is None

    @patch("aioboto3.Session")
    async def test_publish_task_with_string_attributes(self, mock_session_class):
        """Test publishing with string message attributes."""
        # Mock SQS client
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={
            "MessageId": "msg-789"
        })
        mock_sqs.__aenter__.return_value = mock_sqs
        mock_sqs.__aexit__.return_value = AsyncMock()

        # Mock session
        mock_session = MagicMock()
        mock_session.client.return_value = mock_sqs
        mock_session_class.return_value = mock_session

        # Test with different attribute types
        message_attributes = {
            "TaskType": "test_task",
            "Priority": "normal",
            "RetryCount": 3
        }

        # Execute
        result = await sqs_client.publish_task(
            queue_name="test-queue",
            message_body={"test": "data"},
            message_attributes=message_attributes
        )

        # Assertions
        assert result == "msg-789"

        # Verify attribute formatting
        call_args = mock_sqs.send_message.call_args
        formatted_attrs = call_args.kwargs["MessageAttributes"]
        assert formatted_attrs["TaskType"]["DataType"] == "String"
        assert formatted_attrs["RetryCount"]["DataType"] == "Number"

    @patch("aioboto3.Session")
    async def test_publish_task_without_attributes(self, mock_session_class):
        """Test publishing without message attributes."""
        # Mock SQS client
        mock_sqs = AsyncMock()
        mock_sqs.send_message = AsyncMock(return_value={
            "MessageId": "msg-no-attrs"
        })
        mock_sqs.__aenter__.return_value = mock_sqs
        mock_sqs.__aexit__.return_value = AsyncMock()

        # Mock session
        mock_session = MagicMock()
        mock_session.client.return_value = mock_sqs
        mock_session_class.return_value = mock_session

        # Execute without attributes
        result = await sqs_client.publish_task(
            queue_name="test-queue",
            message_body={"test": "data"},
            message_attributes=None
        )

        # Assertions
        assert result == "msg-no-attrs"

        # Verify no MessageAttributes in call
        call_args = mock_sqs.send_message.call_args
        assert "MessageAttributes" not in call_args.kwargs
