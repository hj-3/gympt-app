import logging
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptService:
    """Service for rendering AI prompts using Jinja2 templates."""

    def __init__(self):
        # Get prompts directory path
        prompts_dir = Path(__file__).parent.parent / "prompts"

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape(['md', 'txt']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        logger.info(f"Initialized PromptService with templates from: {prompts_dir}")

    def render_workout_prompt(
        self,
        user_profile: Dict[str, Any],
        request: Dict[str, Any]
    ) -> str:
        """
        Render workout plan prompt.

        Args:
            user_profile: User profile data from backend
            request: Workout recommendation request

        Returns:
            Rendered prompt string
        """
        try:
            template = self.env.get_template("workout_plan.md")
            prompt = template.render(
                user_profile=user_profile,
                request=request
            )
            return prompt

        except Exception as e:
            logger.error(f"Failed to render workout prompt: {e}")
            # Fallback to basic prompt
            return self._fallback_workout_prompt(request)

    def render_posture_prompt(
        self,
        request: Dict[str, Any]
    ) -> str:
        """
        Render posture feedback prompt.

        Args:
            request: Posture feedback request

        Returns:
            Rendered prompt string
        """
        try:
            template = self.env.get_template("posture_feedback.md")
            prompt = template.render(request=request)
            return prompt

        except Exception as e:
            logger.error(f"Failed to render posture prompt: {e}")
            # Fallback to basic prompt
            return self._fallback_posture_prompt(request)

    def render_report_prompt(
        self,
        user_data: Dict[str, Any],
        request: Dict[str, Any]
    ) -> str:
        """
        Render report generation prompt.

        Args:
            user_data: Combined user data (profile, body, goals)
            request: Report generation request

        Returns:
            Rendered prompt string
        """
        try:
            template = self.env.get_template("report_summary.md")
            prompt = template.render(
                user_data=user_data,
                request=request
            )
            return prompt

        except Exception as e:
            logger.error(f"Failed to render report prompt: {e}")
            # Fallback to basic prompt
            return self._fallback_report_prompt(user_data, request)

    def _fallback_workout_prompt(self, request: Dict[str, Any]) -> str:
        """Fallback workout prompt if template fails."""
        return f"""Generate a personalized workout plan:

Goal: {request.get('goal', 'general fitness')}
Fitness Level: {request.get('fitness_level', 'intermediate')}
Days per week: {request.get('days_per_week', 3)}
Equipment: {', '.join(request.get('equipment_available', [])) or 'bodyweight'}

Provide structured workout plan with exercises, sets, reps, and progression."""

    def _fallback_posture_prompt(self, request: Dict[str, Any]) -> str:
        """Fallback posture prompt if template fails."""
        return f"""Analyze exercise form:

Exercise: {request.get('exercise_name', 'unknown')}
Issues detected: {', '.join(request.get('detected_issues', []))}
Score: {request.get('posture_score', 0)}/10

Provide corrections and safety recommendations."""

    def _fallback_report_prompt(
        self,
        user_data: Dict[str, Any],
        request: Dict[str, Any]
    ) -> str:
        """Fallback report prompt if template fails."""
        return f"""Generate fitness progress report:

Period: {request.get('period_start')} to {request.get('period_end')}
User data: {user_data}

Provide insights, achievements, and recommendations."""


# Singleton instance
prompt_service = PromptService()
