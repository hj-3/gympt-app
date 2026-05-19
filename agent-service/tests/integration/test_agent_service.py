import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.agent_service import agent_service


@pytest.mark.asyncio
class TestAgentService:
    """Integration tests for AgentService."""

    @patch("app.services.agent_service.bedrock_client")
    @patch("app.services.agent_service.backend_client")
    @patch("app.services.agent_service.dynamodb_client")
    @patch("app.services.agent_service.cache_service")
    async def test_generate_workout_plan_success(
        self,
        mock_cache,
        mock_dynamodb,
        mock_backend,
        mock_bedrock
    ):
        """Test successful workout plan generation."""
        # Mock cache miss
        mock_cache.generate_cache_key.return_value = "workout_test_key"
        mock_cache.get_cached_response = AsyncMock(return_value=None)
        mock_cache.set_cached_response = AsyncMock(return_value=True)

        # Mock backend user profile
        mock_backend.get_user_profile = AsyncMock(return_value={
            "user_id": "user123",
            "name": "Test User",
            "age": 30,
            "fitness_experience": "intermediate"
        })

        # Mock Bedrock response
        mock_bedrock.invoke_model = AsyncMock(return_value={
            "content": "Detailed workout plan...",
            "model": "claude-3-5-sonnet",
            "usage": {"input_tokens": 100, "output_tokens": 500}
        })

        # Mock DynamoDB logging
        mock_dynamodb.log_interaction = AsyncMock(return_value=True)

        # Test workout request
        workout_request = {
            "goal": "muscle_gain",
            "fitness_level": "intermediate",
            "days_per_week": 4,
            "equipment_available": ["barbell", "dumbbells"]
        }

        # Execute
        result = await agent_service.generate_workout_plan(
            user_id="user123",
            workout_request=workout_request,
            use_cache=True
        )

        # Assertions
        assert result is not None
        assert result["recommendation"] == "Detailed workout plan..."
        assert result["model_used"] == "claude-3-5-sonnet"
        assert result["cached"] is False
        assert "interaction_id" in result

        # Verify calls
        mock_backend.get_user_profile.assert_called_once_with("user123", None)
        mock_bedrock.invoke_model.assert_called_once()
        mock_dynamodb.log_interaction.assert_called_once()
        mock_cache.set_cached_response.assert_called_once()

    @patch("app.services.agent_service.bedrock_client")
    @patch("app.services.agent_service.dynamodb_client")
    async def test_generate_posture_feedback_high_severity(
        self,
        mock_dynamodb,
        mock_bedrock
    ):
        """Test posture feedback with high severity detection."""
        # Mock Bedrock response with severe issues
        mock_bedrock.invoke_model = AsyncMock(return_value={
            "content": "SEVERE form breakdown detected! STOP immediately to prevent injury...",
            "model": "claude-3-5-sonnet",
            "usage": {"input_tokens": 50, "output_tokens": 200}
        })

        # Mock DynamoDB logging
        mock_dynamodb.log_interaction = AsyncMock(return_value=True)

        # Test posture request
        posture_request = {
            "session_id": "session456",
            "exercise_name": "Squat",
            "posture_score": 3.0,
            "detected_issues": ["knee valgus", "excessive forward lean"]
        }

        # Execute
        result = await agent_service.generate_posture_feedback(
            user_id="user123",
            posture_request=posture_request
        )

        # Assertions
        assert result is not None
        assert result["severity"] == "high"
        assert "severe" in result["feedback"].lower() or "stop" in result["feedback"].lower()
        assert result["model_used"] == "claude-3-5-sonnet"

        # Verify calls
        mock_bedrock.invoke_model.assert_called_once()
        mock_dynamodb.log_interaction.assert_called_once()

    @patch("app.services.agent_service.bedrock_client")
    @patch("app.services.agent_service.backend_client")
    @patch("app.services.agent_service.dynamodb_client")
    @patch("app.services.agent_service.sqs_client")
    async def test_generate_report_with_sqs_publish(
        self,
        mock_sqs,
        mock_dynamodb,
        mock_backend,
        mock_bedrock
    ):
        """Test report generation with SQS task publishing."""
        # Mock backend user data
        mock_backend.get_user_data = AsyncMock(return_value={
            "profile": {"name": "Test User", "age": 30},
            "body_profile": {"weight_kg": 75, "height_cm": 175},
            "goals": [{"goal_type": "weight_loss", "target_value": 70}]
        })

        # Mock Bedrock response
        mock_bedrock.invoke_model = AsyncMock(return_value={
            "content": "Excellent progress this month!\n\nKey Insights:\n- Consistency improved\n- Strength gains\n\nRecommendations:\n- Increase volume\n- Focus on recovery",
            "model": "claude-3-5-sonnet",
            "usage": {"input_tokens": 150, "output_tokens": 400}
        })

        # Mock DynamoDB and SQS
        mock_dynamodb.log_interaction = AsyncMock(return_value=True)
        mock_sqs.publish_report_generation_task = AsyncMock(return_value="msg-123")

        # Test report request
        report_request = {
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "include_sections": ["summary", "workouts", "progress"]
        }

        # Execute
        result = await agent_service.generate_report(
            user_id="user123",
            report_request=report_request
        )

        # Assertions
        assert result is not None
        assert "report_summary" in result
        assert len(result["key_insights"]) > 0
        assert len(result["recommendations"]) > 0
        assert "task_id" in result

        # Verify calls
        mock_backend.get_user_data.assert_called_once()
        mock_bedrock.invoke_model.assert_called_once()
        mock_dynamodb.log_interaction.assert_called_once()
        mock_sqs.publish_report_generation_task.assert_called_once()

    @patch("app.services.agent_service.bedrock_client")
    @patch("app.services.agent_service.cache_service")
    async def test_generate_workout_plan_with_cache_hit(
        self,
        mock_cache,
        mock_bedrock
    ):
        """Test workout plan generation with cache hit."""
        # Mock cache hit
        cached_data = {
            "recommendation": "Cached workout plan...",
            "model_used": "claude-3-5-sonnet",
            "cached": False,
            "interaction_id": "cached-123"
        }
        mock_cache.generate_cache_key.return_value = "workout_cache_key"
        mock_cache.get_cached_response = AsyncMock(return_value=cached_data)

        # Test workout request
        workout_request = {
            "goal": "endurance",
            "fitness_level": "beginner",
            "days_per_week": 3,
            "equipment_available": []
        }

        # Execute
        result = await agent_service.generate_workout_plan(
            user_id="user123",
            workout_request=workout_request,
            use_cache=True
        )

        # Assertions
        assert result is not None
        assert result["cached"] is True
        assert result["recommendation"] == "Cached workout plan..."

        # Verify Bedrock was NOT called
        mock_bedrock.invoke_model.assert_not_called()

    @patch("app.services.agent_service.bedrock_client")
    async def test_generate_workout_plan_bedrock_failure(
        self,
        mock_bedrock
    ):
        """Test workout plan generation handles Bedrock failure."""
        # Mock Bedrock failure
        mock_bedrock.invoke_model = AsyncMock(
            side_effect=Exception("Bedrock service unavailable")
        )

        # Test workout request
        workout_request = {
            "goal": "general_fitness",
            "fitness_level": "intermediate",
            "days_per_week": 3,
            "equipment_available": []
        }

        # Execute and expect exception
        with pytest.raises(Exception) as exc_info:
            await agent_service.generate_workout_plan(
                user_id="user123",
                workout_request=workout_request,
                use_cache=False
            )

        assert "Bedrock service unavailable" in str(exc_info.value)
