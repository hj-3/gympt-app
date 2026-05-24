"""
WebSocket client to send feedback to backend API
"""
import httpx
from typing import Dict
from ..config.settings import settings


class WebSocketClient:
    """Client to push posture feedback to backend WebSocket"""

    def __init__(self):
        self.backend_url = settings.BACKEND_API_URL
        self.client = httpx.AsyncClient(timeout=5.0)

    async def send_feedback(
        self,
        session_id: str,
        user_id: str,
        exercise: str,
        rep_count: int,
        form_score: float,
        is_valid: bool,
        feedback: list,
        angles: Dict[str, float],
        message_type: str = "feedback",
    ) -> bool:
        """
        Send posture feedback to backend WebSocket

        Args:
            session_id: Workout session ID
            user_id: User identifier
            exercise: Exercise name
            rep_count: Current rep count
            form_score: Form score (0-100)
            is_valid: Whether form is valid
            feedback: List of feedback messages
            angles: Joint angles
            message_type: Type of message (feedback, rep_complete, session_end)

        Returns:
            True if successful
        """
        try:
            payload = {
                "sessionId": session_id,
                "userId": user_id,
                "exercise": exercise,
                "repCount": rep_count,
                "formScore": form_score,
                "isValid": is_valid,
                "feedback": feedback,
                "angles": angles,
                "messageType": message_type,
            }

            response = await self.client.post(
                f"{self.backend_url}/ws/feedback",
                json=payload,
            )

            if response.status_code == 200:
                return True
            else:
                print(f"Failed to send feedback: {response.status_code}")
                return False

        except Exception as e:
            print(f"Error sending feedback to WebSocket: {e}")
            return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
