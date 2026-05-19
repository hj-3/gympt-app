from typing import Dict, Any, List
import logging
import json
from datetime import datetime

from app.clients.redis_client import redis_client

logger = logging.getLogger(__name__)


class FeedbackService:
    """Generate and publish posture feedback."""
    
    FEEDBACK_CHANNEL = "posture-feedback"
    
    async def generate_feedback(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate human-readable feedback from analysis.
        
        Args:
            analysis: Analysis result with score and issues
            
        Returns:
            Formatted feedback
        """
        score = analysis.get("score", 0)
        issues = analysis.get("issues", [])
        
        if score >= 9.0:
            overall = "Excellent form! Keep it up."
            priority = "maintain"
        elif score >= 7.0:
            overall = "Good form with minor areas to improve."
            priority = "optimize"
        elif score >= 5.0:
            overall = "Form needs attention to prevent injury."
            priority = "correct"
        else:
            overall = "Stop and review form immediately."
            priority = "urgent"
        
        # Extract corrections from issues
        corrections = []
        for issue in issues:
            corrections.append({
                "issue": issue.get("type"),
                "severity": issue.get("severity"),
                "correction": issue.get("correction"),
                "description": issue.get("description")
            })
        
        return {
            "overall": overall,
            "priority": priority,
            "score": score,
            "corrections": corrections,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def publish_feedback(
        self,
        session_id: str,
        analysis: Dict[str, Any],
        feedback: Dict[str, Any]
    ):
        """
        Publish feedback to Redis Pub/Sub.
        
        Subscribers can receive real-time feedback updates.
        """
        try:
            message = {
                "session_id": session_id,
                "analysis": analysis,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Publish to Redis channel
            await redis_client.publish(
                self.FEEDBACK_CHANNEL,
                json.dumps(message)
            )
            
            logger.debug(f"Published feedback for session: {session_id}")
        
        except Exception as e:
            logger.error(f"Failed to publish feedback: {e}")
    
    async def get_feedback_summary(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get summarized feedback for a session.
        
        Could be used for end-of-session reports.
        """
        # This would aggregate feedback from Redis or DynamoDB
        return {
            "session_id": session_id,
            "summary": "Session feedback summary",
            "total_issues": 0,
            "average_score": 8.0
        }
