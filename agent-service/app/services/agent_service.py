import logging
import uuid
from typing import Dict, Any, Optional
from app.clients.bedrock_client import bedrock_client
from app.clients.dynamodb_client import dynamodb_client
from app.clients.sqs_client import sqs_client
from app.clients.backend_client import backend_client
from app.services.cache_service import cache_service
from app.services.prompt_service import prompt_service

logger = logging.getLogger(__name__)


class AgentService:
    """Core service for AI agent operations."""

    async def generate_workout_plan(
        self,
        user_id: str,
        workout_request: Dict[str, Any],
        internal_token: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate personalized workout plan.

        Args:
            user_id: User identifier
            workout_request: Workout recommendation request
            internal_token: JWT token for backend API
            use_cache: Whether to use caching

        Returns:
            Workout recommendation with metadata
        """
        interaction_id = str(uuid.uuid4())

        try:
            # Check cache first
            if use_cache:
                cache_key = cache_service.generate_cache_key(
                    "workout_recommend",
                    user_id,
                    workout_request
                )
                cached = await cache_service.get_cached_response(cache_key)
                if cached:
                    return {
                        **cached,
                        "cached": True,
                        "interaction_id": interaction_id
                    }

            # Fetch user profile from backend
            user_profile = await backend_client.get_user_profile(
                user_id,
                internal_token
            )

            # Render prompt
            prompt = prompt_service.render_workout_prompt(
                user_profile or {},
                workout_request
            )

            # Call Bedrock
            bedrock_response = await bedrock_client.invoke_model(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7,
                system="You are an expert personal trainer with deep knowledge of exercise science and program design."
            )

            # Build response
            result = {
                "recommendation": bedrock_response["content"],
                "model_used": bedrock_response["model"],
                "cached": False,
                "interaction_id": interaction_id
            }

            # Log to DynamoDB (non-blocking)
            await dynamodb_client.log_interaction(
                user_id=user_id,
                interaction_type="workout_recommend",
                request_data=workout_request,
                response_data={"recommendation": bedrock_response["content"]},
                model_id=bedrock_response["model"],
                tokens_used=bedrock_response.get("usage", {})
            )

            # Cache response
            if use_cache:
                await cache_service.set_cached_response(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Failed to generate workout plan: {e}")
            raise

    async def generate_posture_feedback(
        self,
        user_id: str,
        posture_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate posture feedback for exercise form.

        Args:
            user_id: User identifier
            posture_request: Posture feedback request

        Returns:
            Posture feedback with corrections
        """
        interaction_id = str(uuid.uuid4())

        try:
            # Render prompt
            prompt = prompt_service.render_posture_prompt(posture_request)

            # Call Bedrock
            bedrock_response = await bedrock_client.invoke_model(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.5,
                system="You are an expert movement coach specializing in exercise form and injury prevention."
            )

            # Parse response for severity
            content = bedrock_response["content"].lower()
            if "severe" in content or "danger" in content or "stop" in content:
                severity = "high"
            elif "caution" in content or "moderate" in content:
                severity = "medium"
            else:
                severity = "low"

            # Build response
            result = {
                "feedback": bedrock_response["content"],
                "corrections": posture_request.get("detected_issues", []),
                "severity": severity,
                "model_used": bedrock_response["model"],
                "interaction_id": interaction_id
            }

            # Log to DynamoDB (non-blocking)
            await dynamodb_client.log_interaction(
                user_id=user_id,
                interaction_type="posture_feedback",
                request_data=posture_request,
                response_data={"feedback": bedrock_response["content"], "severity": severity},
                model_id=bedrock_response["model"],
                tokens_used=bedrock_response.get("usage", {})
            )

            return result

        except Exception as e:
            logger.error(f"Failed to generate posture feedback: {e}")
            raise

    async def generate_report(
        self,
        user_id: str,
        report_request: Dict[str, Any],
        internal_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate fitness progress report.

        Args:
            user_id: User identifier
            report_request: Report generation request
            internal_token: JWT token for backend API

        Returns:
            Report summary with task ID for full report
        """
        interaction_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        try:
            # Fetch user data from backend
            user_data = await backend_client.get_user_data(
                user_id,
                internal_token
            )

            # Add mock workout data (in real scenario, fetch from workout service)
            user_data["workouts_completed"] = 0  # Placeholder
            user_data["body_profile_changes"] = {}  # Placeholder

            # Render prompt
            prompt = prompt_service.render_report_prompt(
                user_data,
                report_request
            )

            # Call Bedrock
            bedrock_response = await bedrock_client.invoke_model(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.6,
                system="You are a fitness analytics expert who provides actionable insights based on workout data."
            )

            # Parse response for key insights
            content = bedrock_response["content"]
            insights = self._extract_insights(content)
            recommendations = self._extract_recommendations(content)

            # Build response
            result = {
                "report_summary": content[:500],  # First 500 chars as summary
                "key_insights": insights,
                "recommendations": recommendations,
                "model_used": bedrock_response["model"],
                "task_id": task_id,
                "interaction_id": interaction_id
            }

            # Log to DynamoDB (non-blocking)
            await dynamodb_client.log_interaction(
                user_id=user_id,
                interaction_type="report_generation",
                request_data=report_request,
                response_data={"summary": result["report_summary"]},
                model_id=bedrock_response["model"],
                tokens_used=bedrock_response.get("usage", {})
            )

            # Publish to SQS for full report generation (non-blocking)
            await sqs_client.publish_report_generation_task(
                user_id=user_id,
                report_id=task_id,
                period_start=report_request.get("period_start", ""),
                period_end=report_request.get("period_end", ""),
                report_data={
                    "summary": content,
                    "user_data": user_data,
                    "request": report_request
                }
            )

            return result

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise

    def _extract_insights(self, content: str) -> list:
        """Extract key insights from report content."""
        insights = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                insights.append(line[2:])
            elif line and len(insights) < 5:  # Max 5 insights
                insights.append(line)

        return insights[:5]

    def _extract_recommendations(self, content: str) -> list:
        """Extract recommendations from report content."""
        recommendations = []
        in_recommendations = False

        for line in content.split("\n"):
            line = line.strip()
            if "recommendation" in line.lower():
                in_recommendations = True
                continue
            if in_recommendations and (line.startswith("- ") or line.startswith("* ")):
                recommendations.append(line[2:])

        return recommendations[:5]


# Singleton instance
agent_service = AgentService()
