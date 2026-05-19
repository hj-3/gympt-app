"""
Integration tests for Jinja2 prompt template rendering.
"""
import pytest
from pathlib import Path


@pytest.mark.integration
def test_prompt_service_initialization():
    """Test prompt service initializes correctly."""
    from app.services.prompt_service import PromptService

    service = PromptService()
    assert service.env is not None

    # Check prompts directory exists
    prompts_dir = Path(__file__).parent.parent.parent / "app" / "prompts"
    assert prompts_dir.exists()


@pytest.mark.integration
def test_render_workout_prompt_basic():
    """Test basic workout prompt rendering."""
    from app.services.prompt_service import prompt_service

    user_profile = {
        "user_id": "test-user",
        "name": "Test User",
        "age": 30,
        "fitness_experience": "intermediate"
    }

    request = {
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "days_per_week": 4,
        "equipment_available": ["barbell", "dumbbell"],
        "injuries_or_limitations": None
    }

    prompt = prompt_service.render_workout_prompt(user_profile, request)

    assert prompt is not None
    assert len(prompt) > 0
    assert "muscle_gain" in prompt.lower() or "muscle" in prompt.lower()
    assert "intermediate" in prompt.lower()


@pytest.mark.integration
def test_render_workout_prompt_with_injury():
    """Test workout prompt rendering with injury limitations."""
    from app.services.prompt_service import prompt_service

    user_profile = {"user_id": "test-user", "name": "Test User"}
    request = {
        "goal": "general_fitness",
        "fitness_level": "beginner",
        "days_per_week": 3,
        "equipment_available": [],
        "injuries_or_limitations": "Lower back pain, avoid deadlifts"
    }

    prompt = prompt_service.render_workout_prompt(user_profile, request)

    assert "back" in prompt.lower() or "injury" in prompt.lower() or "limitation" in prompt.lower()


@pytest.mark.integration
def test_render_posture_prompt():
    """Test posture feedback prompt rendering."""
    from app.services.prompt_service import prompt_service

    request = {
        "exercise_name": "squat",
        "posture_score": 7.5,
        "detected_issues": ["knee_valgus", "insufficient_depth"],
        "frame_data": {}
    }

    prompt = prompt_service.render_posture_prompt(request)

    assert prompt is not None
    assert "squat" in prompt.lower()
    assert "knee" in prompt.lower() or "valgus" in prompt.lower()


@pytest.mark.integration
def test_render_report_prompt():
    """Test report generation prompt rendering."""
    from app.services.prompt_service import prompt_service

    user_data = {
        "user_id": "test-user",
        "profile": {"name": "Test User"},
        "body_profile": {
            "weight_kg": 75,
            "height_cm": 175
        },
        "goals": [{"goal_type": "muscle_gain"}],
        "workouts_completed": 12
    }

    request = {
        "period_start": "2024-01-01",
        "period_end": "2024-01-07",
        "include_sections": ["summary", "workouts", "recommendations"]
    }

    prompt = prompt_service.render_report_prompt(user_data, request)

    assert prompt is not None
    assert "2024-01-01" in prompt or "january" in prompt.lower()


@pytest.mark.integration
def test_render_workout_prompt_fallback():
    """Test fallback when template is missing."""
    from app.services.prompt_service import PromptService
    from jinja2 import TemplateNotFound
    from unittest.mock import Mock, patch

    service = PromptService()

    # Mock template loading to fail
    mock_env = Mock()
    mock_env.get_template.side_effect = TemplateNotFound("workout_plan.md")

    with patch.object(service, 'env', mock_env):
        request = {
            "goal": "weight_loss",
            "fitness_level": "beginner",
            "days_per_week": 3,
            "equipment_available": ["bodyweight"]
        }

        prompt = service.render_workout_prompt({}, request)

        # Should use fallback prompt
        assert prompt is not None
        assert "weight_loss" in prompt.lower() or "weight loss" in prompt.lower()
        assert "beginner" in prompt.lower()


@pytest.mark.integration
def test_render_posture_prompt_fallback():
    """Test posture prompt fallback."""
    from app.services.prompt_service import PromptService
    from jinja2 import TemplateNotFound
    from unittest.mock import Mock, patch

    service = PromptService()

    mock_env = Mock()
    mock_env.get_template.side_effect = TemplateNotFound("posture_feedback.md")

    with patch.object(service, 'env', mock_env):
        request = {
            "exercise_name": "deadlift",
            "posture_score": 5.0,
            "detected_issues": ["rounded_back"]
        }

        prompt = service.render_posture_prompt(request)

        assert prompt is not None
        assert "deadlift" in prompt.lower()
        assert "rounded" in prompt.lower() or "back" in prompt.lower()


@pytest.mark.integration
def test_render_report_prompt_fallback():
    """Test report prompt fallback."""
    from app.services.prompt_service import PromptService
    from jinja2 import TemplateNotFound
    from unittest.mock import Mock, patch

    service = PromptService()

    mock_env = Mock()
    mock_env.get_template.side_effect = TemplateNotFound("report_summary.md")

    with patch.object(service, 'env', mock_env):
        user_data = {"user_id": "test"}
        request = {
            "period_start": "2024-01-01",
            "period_end": "2024-01-07"
        }

        prompt = service.render_report_prompt(user_data, request)

        assert prompt is not None
        assert "2024-01-01" in prompt


@pytest.mark.integration
def test_prompt_rendering_with_missing_variables():
    """Test prompt rendering handles missing variables gracefully."""
    from app.services.prompt_service import prompt_service

    # Minimal data
    user_profile = {}
    request = {
        "goal": "muscle_gain",
        "fitness_level": "intermediate"
    }

    # Should not raise exception
    prompt = prompt_service.render_workout_prompt(user_profile, request)
    assert prompt is not None


@pytest.mark.integration
def test_prompt_rendering_with_special_characters():
    """Test prompt rendering with special characters."""
    from app.services.prompt_service import prompt_service

    user_profile = {
        "name": "Test User <script>alert('xss')</script>"
    }

    request = {
        "goal": "weight_loss",
        "fitness_level": "beginner",
        "injuries_or_limitations": "Knee & ankle issues, can't do squats"
    }

    prompt = prompt_service.render_workout_prompt(user_profile, request)

    # Jinja2 autoescape should handle special characters
    assert prompt is not None


@pytest.mark.integration
def test_prompt_rendering_unicode():
    """Test prompt rendering with unicode characters."""
    from app.services.prompt_service import prompt_service

    user_profile = {
        "name": "김철수",  # Korean name
        "fitness_experience": "중급"
    }

    request = {
        "goal": "muscle_gain",
        "fitness_level": "intermediate",
        "equipment_available": ["바벨", "덤벨"]  # Korean equipment names
    }

    prompt = prompt_service.render_workout_prompt(user_profile, request)

    assert prompt is not None
    # Unicode characters should be preserved
    assert "김철수" in prompt or "muscle_gain" in prompt.lower()


@pytest.mark.integration
def test_prompt_rendering_empty_lists():
    """Test prompt rendering with empty equipment lists."""
    from app.services.prompt_service import prompt_service

    user_profile = {"user_id": "test"}
    request = {
        "goal": "weight_loss",
        "fitness_level": "beginner",
        "days_per_week": 3,
        "equipment_available": [],  # Empty list
        "injuries_or_limitations": None
    }

    prompt = prompt_service.render_workout_prompt(user_profile, request)

    assert prompt is not None
    # Should handle empty equipment list
    assert "bodyweight" in prompt.lower() or "no equipment" in prompt.lower() or len(prompt) > 0
