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

            # Call Bedrock Agent (not direct model invocation)
            session_id = f"{user_id}-workout-{interaction_id[:8]}"
            agent_response = await bedrock_client.invoke_agent(
                session_id=session_id,
                input_text=prompt,
                enable_trace=False
            )

            # Build response
            result = {
                "recommendation": agent_response["completion"],
                "model_used": "bedrock-agent",
                "cached": False,
                "interaction_id": interaction_id,
                "session_id": session_id
            }

            # Log to DynamoDB (non-blocking)
            await dynamodb_client.log_interaction(
                user_id=user_id,
                interaction_type="workout_recommend",
                request_data=workout_request,
                response_data={"recommendation": agent_response["completion"]},
                model_id="bedrock-agent",
                tokens_used={}
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

            # Call Bedrock Agent
            session_id = f"{user_id}-posture-{interaction_id[:8]}"
            session_attributes = {
                "exercise": posture_request.get("exercise_name", ""),
                "rep_count": str(posture_request.get("rep_count", 0)),
            }
            agent_response = await bedrock_client.invoke_agent(
                session_id=session_id,
                input_text=prompt,
                user_id=user_id,
                session_attributes=session_attributes,
                enable_trace=False
            )

            content = agent_response["completion"]

            # Parse response for severity
            content_lower = content.lower()
            if "severe" in content_lower or "danger" in content_lower or "stop" in content_lower:
                severity = "high"
            elif "caution" in content_lower or "moderate" in content_lower:
                severity = "medium"
            else:
                severity = "low"

            # Build response
            result = {
                "feedback": content,
                "corrections": posture_request.get("detected_issues", []),
                "severity": severity,
                "model_used": "bedrock-agent",
                "interaction_id": interaction_id,
                "session_id": session_id
            }

            # Log to DynamoDB (non-blocking)
            await dynamodb_client.log_interaction(
                user_id=user_id,
                interaction_type="posture_feedback",
                request_data=posture_request,
                response_data={"feedback": content, "severity": severity},
                model_id="bedrock-agent",
                tokens_used={}
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

            # Call Bedrock Agent
            session_id = f"{user_id}-report-{interaction_id[:8]}"
            session_attributes = {
                "report_type": report_request.get("report_type", "weekly"),
                "period_start": report_request.get("period_start", ""),
                "period_end": report_request.get("period_end", ""),
            }
            agent_response = await bedrock_client.invoke_agent(
                session_id=session_id,
                input_text=prompt,
                user_id=user_id,
                session_attributes=session_attributes,
                enable_trace=False
            )

            content = agent_response["completion"]
            insights = self._extract_insights(content)
            recommendations = self._extract_recommendations(content)

            # Build response
            result = {
                "report_summary": content[:500],
                "key_insights": insights,
                "recommendations": recommendations,
                "model_used": "bedrock-agent",
                "task_id": task_id,
                "interaction_id": interaction_id,
                "session_id": session_id
            }

            # Log to DynamoDB (non-blocking)
            await dynamodb_client.log_interaction(
                user_id=user_id,
                interaction_type="report_generation",
                request_data=report_request,
                response_data={"summary": result["report_summary"]},
                model_id="bedrock-agent",
                tokens_used={}
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
