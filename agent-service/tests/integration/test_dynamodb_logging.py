import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.clients.dynamodb_client import dynamodb_client


@pytest.mark.asyncio
class TestDynamoDBLogging:
    """Integration tests for DynamoDB interaction logging."""

    @patch("aioboto3.Session")
    async def test_log_interaction_success(self, mock_session_class):
        """Test successful interaction logging."""
        # Mock DynamoDB table
        mock_table = AsyncMock()
        mock_table.put_item = AsyncMock()

        # Mock resource
        mock_resource = AsyncMock()
        mock_resource.Table = AsyncMock(return_value=mock_table)
        mock_resource.__aenter__.return_value = mock_resource
        mock_resource.__aexit__.return_value = AsyncMock()

        # Mock session
        mock_session = MagicMock()
        mock_session.resource.return_value = mock_resource
        mock_session_class.return_value = mock_session

        # Test data
        request_data = {
            "goal": "muscle_gain",
            "fitness_level": "intermediate"
        }
        response_data = {
            "recommendation": "Workout plan..."
        }
        tokens_used = {
            "input_tokens": 100,
            "output_tokens": 500
        }

        # Execute
        result = await dynamodb_client.log_interaction(
            user_id="user123",
            interaction_type="workout_recommend",
            request_data=request_data,
            response_data=response_data,
            model_id="claude-3-5-sonnet",
            tokens_used=tokens_used
        )

        # Assertions
        assert result is True
        mock_table.put_item.assert_called_once()

        # Verify item structure
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs["Item"]
        assert item["user_id"] == "user123"
        assert item["interaction_type"] == "workout_recommend"
        assert item["model_id"] == "claude-3-5-sonnet"
        assert "timestamp" in item

    @patch("aioboto3.Session")
    async def test_log_interaction_handles_failure(self, mock_session_class):
        """Test graceful handling of DynamoDB failure."""
        # Mock session that raises exception
        mock_session = MagicMock()
        mock_session.resource.side_effect = Exception("DynamoDB unavailable")
        mock_session_class.return_value = mock_session

        # Execute
        result = await dynamodb_client.log_interaction(
            user_id="user123",
            interaction_type="posture_feedback",
            request_data={},
            response_data={},
            model_id="claude-3-5-sonnet"
        )

        # Should return False but not raise exception (graceful degradation)
        assert result is False

    @patch("aioboto3.Session")
    async def test_get_user_interactions_by_type(self, mock_session_class):
        """Test retrieving user interactions filtered by type."""
        # Mock query response
        mock_table = AsyncMock()
        mock_table.query = AsyncMock(return_value={
            "Items": [
                {
                    "user_id": "user123",
                    "timestamp": "2024-01-15T10:00:00",
                    "interaction_type": "workout_recommend",
                    "request_data": {"goal": "muscle_gain"}
                },
                {
                    "user_id": "user123",
                    "timestamp": "2024-01-14T15:30:00",
                    "interaction_type": "workout_recommend",
                    "request_data": {"goal": "endurance"}
                }
            ]
        })

        # Mock resource
        mock_resource = AsyncMock()
        mock_resource.Table = AsyncMock(return_value=mock_table)
        mock_resource.__aenter__.return_value = mock_resource
        mock_resource.__aexit__.return_value = AsyncMock()

        # Mock session
        mock_session = MagicMock()
        mock_session.resource.return_value = mock_resource
        mock_session_class.return_value = mock_session

        # Execute
        result = await dynamodb_client.get_user_interactions(
            user_id="user123",
            interaction_type="workout_recommend",
            limit=50
        )

        # Assertions
        assert result is not None
        assert len(result) == 2
        assert all(item["interaction_type"] == "workout_recommend" for item in result)

    @patch("aioboto3.Session")
    async def test_get_user_interactions_all_types(self, mock_session_class):
        """Test retrieving all user interactions without type filter."""
        # Mock query response
        mock_table = AsyncMock()
        mock_table.query = AsyncMock(return_value={
            "Items": [
                {
                    "user_id": "user123",
                    "timestamp": "2024-01-15T10:00:00",
                    "interaction_type": "workout_recommend"
                },
                {
                    "user_id": "user123",
                    "timestamp": "2024-01-14T15:30:00",
                    "interaction_type": "posture_feedback"
                },
                {
                    "user_id": "user123",
                    "timestamp": "2024-01-13T09:00:00",
                    "interaction_type": "report_generation"
                }
            ]
        })

        # Mock resource
        mock_resource = AsyncMock()
        mock_resource.Table = AsyncMock(return_value=mock_table)
        mock_resource.__aenter__.return_value = mock_resource
        mock_resource.__aexit__.return_value = AsyncMock()

        # Mock session
        mock_session = MagicMock()
        mock_session.resource.return_value = mock_resource
        mock_session_class.return_value = mock_session

        # Execute
        result = await dynamodb_client.get_user_interactions(
            user_id="user123",
            interaction_type=None,
            limit=50
        )

        # Assertions
        assert result is not None
        assert len(result) == 3
        assert result[0]["interaction_type"] == "workout_recommend"
        assert result[1]["interaction_type"] == "posture_feedback"
        assert result[2]["interaction_type"] == "report_generation"

    @patch("aioboto3.Session")
    async def test_log_interaction_with_empty_tokens(self, mock_session_class):
        """Test logging interaction without token usage."""
        # Mock DynamoDB table
        mock_table = AsyncMock()
        mock_table.put_item = AsyncMock()

        # Mock resource
        mock_resource = AsyncMock()
        mock_resource.Table = AsyncMock(return_value=mock_table)
        mock_resource.__aenter__.return_value = mock_resource
        mock_resource.__aexit__.return_value = AsyncMock()

        # Mock session
        mock_session = MagicMock()
        mock_session.resource.return_value = mock_resource
        mock_session_class.return_value = mock_session

        # Execute without tokens_used
        result = await dynamodb_client.log_interaction(
            user_id="user123",
            interaction_type="posture_feedback",
            request_data={"exercise": "squat"},
            response_data={"feedback": "Good form"},
            model_id="claude-3-5-sonnet",
            tokens_used=None
        )

        # Assertions
        assert result is True

        # Verify tokens_used defaults to empty dict
        call_args = mock_table.put_item.call_args
        item = call_args.kwargs["Item"]
        assert item["tokens_used"] == {}
