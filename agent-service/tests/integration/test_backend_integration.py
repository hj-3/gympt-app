import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.clients.backend_client import backend_client


@pytest.mark.asyncio
class TestBackendIntegration:
    """Integration tests for Backend API client."""

    @patch("httpx.AsyncClient")
    async def test_get_user_profile_success(self, mock_client_class):
        """Test successful user profile retrieval."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "user123",
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "gender": "male",
            "fitness_experience": "intermediate"
        }
        mock_response.raise_for_status = AsyncMock()

        # Mock client
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Execute
        result = await backend_client.get_user_profile(
            user_id="user123",
            internal_token="test-token"
        )

        # Assertions
        assert result is not None
        assert result["user_id"] == "user123"
        assert result["name"] == "John Doe"
        assert result["fitness_experience"] == "intermediate"

        # Verify call
        mock_client.get.assert_called_once()

    @patch("httpx.AsyncClient")
    async def test_get_body_profile_success(self, mock_client_class):
        """Test successful body profile retrieval."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "user123",
            "height_cm": 175.0,
            "weight_kg": 75.5,
            "body_fat_percentage": 18.5,
            "muscle_mass_kg": 35.2
        }
        mock_response.raise_for_status = AsyncMock()

        # Mock client
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Execute
        result = await backend_client.get_body_profile(
            user_id="user123"
        )

        # Assertions
        assert result is not None
        assert result["height_cm"] == 175.0
        assert result["weight_kg"] == 75.5
        assert result["body_fat_percentage"] == 18.5

    @patch("httpx.AsyncClient")
    async def test_get_workout_goals_success(self, mock_client_class):
        """Test successful workout goals retrieval."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "goal_id": "goal1",
                "user_id": "user123",
                "goal_type": "weight_loss",
                "target_value": 70.0,
                "current_value": 75.5,
                "status": "active"
            },
            {
                "goal_id": "goal2",
                "user_id": "user123",
                "goal_type": "muscle_gain",
                "target_value": 40.0,
                "current_value": 35.2,
                "status": "active"
            }
        ]
        mock_response.raise_for_status = AsyncMock()

        # Mock client
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Execute
        result = await backend_client.get_workout_goals(
            user_id="user123"
        )

        # Assertions
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["goal_type"] == "weight_loss"

    @patch("httpx.AsyncClient")
    async def test_get_user_profile_not_found(self, mock_client_class):
        """Test user profile retrieval with 404 error."""
        # Mock HTTP 404 response
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=AsyncMock(),
            response=mock_response
        )

        # Mock client
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Execute
        result = await backend_client.get_user_profile(
            user_id="nonexistent"
        )

        # Assertions
        assert result is None

    @patch("httpx.AsyncClient")
    async def test_get_user_data_parallel(self, mock_client_class):
        """Test fetching all user data in parallel."""
        # Mock HTTP responses
        profile_response = AsyncMock()
        profile_response.status_code = 200
        profile_response.json.return_value = {"user_id": "user123", "name": "John"}
        profile_response.raise_for_status = AsyncMock()

        body_response = AsyncMock()
        body_response.status_code = 200
        body_response.json.return_value = {"weight_kg": 75.0}
        body_response.raise_for_status = AsyncMock()

        goals_response = AsyncMock()
        goals_response.status_code = 200
        goals_response.json.return_value = [{"goal_type": "weight_loss"}]
        goals_response.raise_for_status = AsyncMock()

        # Mock client with different responses
        mock_client = AsyncMock()
        mock_client.get.side_effect = [
            profile_response,
            body_response,
            goals_response
        ]
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Execute
        result = await backend_client.get_user_data(
            user_id="user123"
        )

        # Assertions
        assert result is not None
        assert result["profile"] is not None
        assert result["body_profile"] is not None
        assert result["goals"] is not None
        assert result["profile"]["name"] == "John"

    @patch("httpx.AsyncClient")
    async def test_retry_logic_on_timeout(self, mock_client_class):
        """Test retry logic for timeout errors."""
        # Mock client that times out twice then succeeds
        mock_client = AsyncMock()
        mock_client.get.side_effect = [
            httpx.TimeoutException("Request timeout"),
            httpx.TimeoutException("Request timeout"),
            AsyncMock(
                status_code=200,
                json=AsyncMock(return_value={"user_id": "user123"}),
                raise_for_status=AsyncMock()
            )
        ]
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        # Execute (should succeed after retries)
        result = await backend_client.get_user_profile(
            user_id="user123"
        )

        # Assertions
        assert result is not None
        assert result["user_id"] == "user123"
        assert mock_client.get.call_count == 3
