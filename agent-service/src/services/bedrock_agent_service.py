"""
Bedrock Agent Service - AWS Bedrock Agent Integration
"""
import boto3
import json
from typing import Dict, Any, Optional
from ..config.settings import settings


class BedrockAgentService:
    """Service for interacting with AWS Bedrock Agent"""

    def __init__(self):
        self.client = boto3.client(
            "bedrock-agent-runtime",
            region_name=settings.BEDROCK_REGION,
        )
        self.agent_id = settings.BEDROCK_AGENT_ID
        self.agent_alias_id = settings.BEDROCK_AGENT_ALIAS_ID

    async def invoke_agent(
        self,
        user_id: str,
        session_id: str,
        input_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock Agent with user input

        Args:
            user_id: User identifier
            session_id: Session identifier
            input_text: User input text
            context: Optional context information

        Returns:
            Agent response with output text and metadata
        """
        try:
            # Prepare session attributes
            session_attributes = {
                "user_id": user_id,
            }
            if context:
                session_attributes.update(context)

            # Invoke agent
            response = self.client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=input_text,
                sessionState={
                    "sessionAttributes": session_attributes,
                },
            )

            # Process streaming response
            output_text = ""
            completion = False
            citations = []
            trace = {}

            event_stream = response.get("completion", [])
            for event in event_stream:
                if "chunk" in event:
                    chunk = event["chunk"]
                    if "bytes" in chunk:
                        output_text += chunk["bytes"].decode("utf-8")

                elif "trace" in event:
                    trace = event["trace"]

                elif "returnControl" in event:
                    # Handle return control for action groups
                    pass

            completion = True

            return {
                "session_id": session_id,
                "output_text": output_text,
                "completion": completion,
                "citations": citations if citations else None,
                "trace": trace if trace else None,
            }

        except Exception as e:
            raise Exception(f"Failed to invoke Bedrock Agent: {str(e)}")

    async def generate_workout_plan(
        self,
        user_id: str,
        session_id: str,
        user_profile: Dict[str, Any],
        goals: list[str],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate personalized workout plan using Bedrock Agent with Knowledge Base

        Args:
            user_id: User identifier
            session_id: Session identifier
            user_profile: User profile information (age, fitness level, etc.)
            goals: List of fitness goals
            constraints: Any constraints (injuries, time availability, etc.)

        Returns:
            Personalized workout plan from agent with RAG-enhanced knowledge
        """
        # Construct prompt for agent
        prompt = f"""
        Generate a personalized workout plan for me.

        My Profile:
        - Age: {user_profile.get('age', 'N/A')}
        - Fitness Level: {user_profile.get('fitnessLevel', 'BEGINNER')}
        - Height: {user_profile.get('heightCm', 'N/A')} cm
        - Weight: {user_profile.get('weightKg', 'N/A')} kg
        - Body Fat: {user_profile.get('bodyFatPercentage', 'N/A')}%

        My Goals: {', '.join(goals)}
        {f"Constraints: {json.dumps(constraints)}" if constraints else ""}

        Please create a weekly workout plan with specific exercises, sets, reps, and safety tips.
        """

        context = {
            "user_profile": json.dumps(user_profile),
            "goals": ','.join(goals),
        }

        return await self.invoke_agent(
            user_id=user_id,
            session_id=session_id,
            input_text=prompt,
            context=context,
        )

    async def analyze_posture_feedback(
        self,
        user_id: str,
        session_id: str,
        exercise: str,
        posture_data: Dict[str, Any],
        rep_count: int,
        previous_feedback: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Analyze posture data and provide real-time feedback using Bedrock Agent

        Args:
            user_id: User identifier
            session_id: Session identifier
            exercise: Exercise name
            posture_data: Posture analysis results (angles, positions)
            rep_count: Current rep count
            previous_feedback: Previous feedback for context

        Returns:
            AI-generated feedback and corrections from agent
        """
        prev_context = ""
        if previous_feedback:
            prev_context = f"\nPrevious feedback: {json.dumps(previous_feedback[-3:])}"

        prompt = f"""
        I'm doing {exercise} exercise. This is rep #{rep_count}.

        My current form metrics:
        {json.dumps(posture_data, indent=2)}
        {prev_context}

        Please analyze my form and provide:
        1. Overall form score (0-100)
        2. Specific corrections if needed
        3. Encouragement
        Keep it concise for real-time feedback.
        """

        context = {
            "exercise": exercise,
            "rep_count": str(rep_count),
        }

        return await self.invoke_agent(
            user_id=user_id,
            session_id=session_id,
            input_text=prompt,
            context=context,
        )

    async def generate_workout_report(
        self,
        user_id: str,
        session_id: str,
        workout_summary: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive workout report with AI insights

        Args:
            user_id: User identifier
            session_id: Session identifier for this report
            workout_summary: Session statistics
            historical_data: Previous sessions for trend analysis

        Returns:
            AI-generated report with insights and recommendations
        """
        history_text = ""
        if historical_data:
            history_text = f"\n\nMy workout history (last {len(historical_data)} sessions):\n"
            for i, session in enumerate(historical_data[-5:], 1):
                history_text += f"Session {i}: {session.get('exercises', 'N/A')} exercises, {session.get('duration', 0)}min, score: {session.get('score', 0)}/10\n"

        prompt = f"""
        Please generate a comprehensive workout report for my session:

        Session Summary:
        - Duration: {workout_summary.get('durationMinutes', 0)} minutes
        - Exercises: {workout_summary.get('exercisesCompleted', 0)}
        - Total Reps: {workout_summary.get('totalReps', 0)}
        - Average Form Score: {workout_summary.get('avgFormScore', 0)}/10
        {history_text}

        Please provide:
        1. Performance highlights
        2. Areas for improvement
        3. Progress trends (if history available)
        4. Recommendations for next workout
        5. Motivational message

        Format as a well-structured report.
        """

        return await self.invoke_agent(
            user_id=user_id,
            session_id=session_id,
            input_text=prompt,
            context={"report_type": "workout_summary"},
        )

    async def chat_interactive(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
    ) -> Dict[str, Any]:
        """
        Interactive chat with PT Agent

        Args:
            user_id: User identifier
            session_id: Conversation session ID
            user_message: User's question or message

        Returns:
            Agent's response (conversational, with memory)
        """
        return await self.invoke_agent(
            user_id=user_id,
            session_id=session_id,
            input_text=user_message,
            context={"interaction_type": "chat"},
        )
