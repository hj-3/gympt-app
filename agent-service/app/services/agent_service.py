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

            # Fetch user profile and body profile from backend in parallel
            import asyncio as _asyncio
            _results = await _asyncio.gather(
                backend_client.get_user_profile(user_id, internal_token),
                backend_client.get_body_profile(user_id, internal_token),
                return_exceptions=True
            )
            user_profile = _results[0] if not isinstance(_results[0], Exception) else {}
            body_profile_data = _results[1] if not isinstance(_results[1], Exception) else {}

            # Merge body profile into user_profile for the prompt template.
            # Values passed directly in workout_request take precedence over what
            # the backend returns (they come from the user's latest 인바디 record).
            merged_profile = dict(user_profile or {})
            if body_profile_data:
                merged_profile.setdefault("height", body_profile_data.get("height") or body_profile_data.get("height_cm"))
                merged_profile.setdefault("weight", body_profile_data.get("weight") or body_profile_data.get("weight_kg"))
                merged_profile.setdefault("body_fat", body_profile_data.get("body_fat") or body_profile_data.get("body_fat_percentage"))
                merged_profile.setdefault("muscle_mass", body_profile_data.get("muscle_mass") or body_profile_data.get("muscle_mass_kg"))
            # Override with values explicitly sent in the request (frontend already loaded latest 인바디)
            for field in ("height", "weight", "body_fat", "muscle_mass"):
                if workout_request.get(field) is not None:
                    merged_profile[field] = workout_request[field]

            # Render prompt
            prompt = prompt_service.render_workout_prompt(
                merged_profile,
                workout_request
            )

            # Call Bedrock Agent (not direct model invocation)
            session_id = f"{user_id}-workout-{interaction_id[:8]}"
            agent_response = await bedrock_client.invoke_agent(
                session_id=session_id,
                input_text=prompt,
                enable_trace=False
            )

            # Extract structured KVS-trackable targets (exercise/sets/reps) from the plan text
            target_exercises = self._extract_target_exercises(agent_response["completion"])

            # Build response
            result = {
                "recommendation": agent_response["completion"],
                "target_exercises": target_exercises,
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

    # Korean exercise name -> KVS-trackable exercise key (matches frontend /workout)
    _TRACKABLE_EXERCISES = {
        "스쿼트": "squat",
        "푸시업": "pushup",
        "푸쉬업": "pushup",
        "런지": "lunge",
        "플랭크": "plank",
    }

    def _extract_target_exercises(self, content: str) -> list:
        """
        Parse the recommendation text and extract structured targets.

        Matches patterns like:
          - "기본 스쿼트: 3세트 x 12-15회"
          - "푸시업 3세트 × 10회"
          - "플랭크: 3세트 x 30초"
          - "스쿼트 (3세트, 12회)"

        Returns a list of {exercise, sets, reps} dicts.
        For plank, 'reps' = target hold seconds (e.g. 30).
        """
        import re

        targets: Dict[str, Dict[str, Any]] = {}

        for line in content.split("\n"):
            for kor_name, key in self._TRACKABLE_EXERCISES.items():
                if kor_name not in line or key in targets:
                    continue

                # "N세트" — look forward and backward from exercise name
                sets_match = re.search(r"(\d+)\s*세트", line)
                sets = int(sets_match.group(1)) if sets_match else 3

                # For plank: look for 초 (seconds) first, then 회 as fallback
                if key == "plank":
                    sec_match = re.search(r"(\d+)(?:\s*[-~x×]\s*\d+)?\s*초", line)
                    if sec_match:
                        reps = int(sec_match.group(1))
                    else:
                        reps = 30  # sensible plank default
                else:
                    # Take the lower bound of a range (e.g. "12-15회" → 12)
                    reps_match = re.search(r"(\d+)(?:\s*[-~]\s*\d+)?\s*(?:회|개)", line)
                    reps = int(reps_match.group(1)) if reps_match else 10

                targets[key] = {
                    "exercise": key,
                    "sets": max(1, sets),
                    "reps": max(1, reps),
                }

        return list(targets.values())

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
