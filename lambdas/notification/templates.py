"""Notification templates for different notification types and channels."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class NotificationTemplate:
    """Base class for notification templates."""

    @staticmethod
    def render_slack(notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Render Slack message payload."""
        templates = {
            "REPORT_READY": SlackTemplates.report_ready,
            "RECOMMENDATION_UPDATE": SlackTemplates.recommendation_update,
            "WORKOUT_COMPLETED": SlackTemplates.workout_completed,
            "POSTURE_ALERT": SlackTemplates.posture_alert,
            "GOAL_ACHIEVED": SlackTemplates.goal_achieved,
        }

        template_func = templates.get(notification_type)
        if template_func:
            return template_func(data)
        else:
            return SlackTemplates.default(notification_type, data)

    @staticmethod
    def render_email(notification_type: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Render email subject and body."""
        templates = {
            "REPORT_READY": EmailTemplates.report_ready,
            "RECOMMENDATION_UPDATE": EmailTemplates.recommendation_update,
            "WORKOUT_COMPLETED": EmailTemplates.workout_completed,
            "POSTURE_ALERT": EmailTemplates.posture_alert,
            "GOAL_ACHIEVED": EmailTemplates.goal_achieved,
        }

        template_func = templates.get(notification_type)
        if template_func:
            return template_func(data)
        else:
            return EmailTemplates.default(notification_type, data)

    @staticmethod
    def render_push(notification_type: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Render push notification payload."""
        templates = {
            "REPORT_READY": PushTemplates.report_ready,
            "RECOMMENDATION_UPDATE": PushTemplates.recommendation_update,
            "WORKOUT_COMPLETED": PushTemplates.workout_completed,
            "POSTURE_ALERT": PushTemplates.posture_alert,
            "GOAL_ACHIEVED": PushTemplates.goal_achieved,
        }

        template_func = templates.get(notification_type)
        if template_func:
            return template_func(data)
        else:
            return PushTemplates.default(notification_type, data)


class SlackTemplates:
    """Slack message templates."""

    @staticmethod
    def report_ready(data: Dict[str, Any]) -> Dict[str, Any]:
        """Report ready template."""
        period = data.get("period", "weekly")
        return {
            "attachments": [
                {
                    "color": "#36a64f",
                    "title": f"Your {period.capitalize()} Workout Report is Ready!",
                    "text": "View your insights and progress analysis.",
                    "fields": [
                        {"title": "Period", "value": period, "short": True},
                        {"title": "User", "value": data.get("userId"), "short": True},
                    ],
                    "footer": "GymPT Analytics",
                }
            ]
        }

    @staticmethod
    def recommendation_update(data: Dict[str, Any]) -> Dict[str, Any]:
        """Recommendation update template."""
        adjustment = data.get("adjustment", "MAINTAIN")
        reason = data.get("reason", "Based on your recent performance")

        color = "#36a64f" if adjustment == "INCREASE" else "#ff9800" if adjustment == "DECREASE" else "#2196f3"
        emoji = "📈" if adjustment == "INCREASE" else "📉" if adjustment == "DECREASE" else "➡️"

        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} Workout Intensity: {adjustment}",
                    "text": reason,
                    "fields": [
                        {"title": "Action", "value": adjustment, "short": True},
                        {"title": "User", "value": data.get("userId"), "short": True},
                    ],
                    "footer": "GymPT Recommendations",
                }
            ]
        }

    @staticmethod
    def workout_completed(data: Dict[str, Any]) -> Dict[str, Any]:
        """Workout completed template."""
        score = data.get("score", "N/A")
        reps = data.get("reps", 0)

        return {
            "attachments": [
                {
                    "color": "#4caf50",
                    "title": "Great Job! Workout Completed",
                    "text": f"{reps} reps completed with a form score of {score}/10",
                    "fields": [
                        {"title": "Form Score", "value": f"{score}/10", "short": True},
                        {"title": "Reps", "value": str(reps), "short": True},
                    ],
                    "footer": "Keep up the great work!",
                }
            ]
        }

    @staticmethod
    def posture_alert(data: Dict[str, Any]) -> Dict[str, Any]:
        """Posture alert template."""
        issues = data.get("issues", [])
        issue_text = ", ".join(issues[:3]) if issues else "Form issues detected"

        return {
            "attachments": [
                {
                    "color": "#ff5722",
                    "title": "Form Alert",
                    "text": f"Issues detected: {issue_text}",
                    "fields": [
                        {"title": "Issues", "value": str(len(issues)), "short": True},
                        {"title": "Session", "value": data.get("sessionId", "N/A"), "short": True},
                    ],
                    "footer": "Review your form",
                }
            ]
        }

    @staticmethod
    def goal_achieved(data: Dict[str, Any]) -> Dict[str, Any]:
        """Goal achieved template."""
        goal = data.get("goal", "workout goal")

        return {
            "attachments": [
                {
                    "color": "#ffc107",
                    "title": "🎉 Congratulations!",
                    "text": f"You achieved your {goal} goal!",
                    "fields": [
                        {"title": "Goal", "value": goal, "short": True},
                        {"title": "User", "value": data.get("userId"), "short": True},
                    ],
                    "footer": "Amazing progress!",
                }
            ]
        }

    @staticmethod
    def default(notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Default template."""
        return {
            "text": f"🔔 {notification_type}",
            "attachments": [
                {
                    "color": "#607d8b",
                    "fields": [
                        {"title": "Type", "value": notification_type, "short": True},
                        {"title": "User", "value": data.get("userId", "N/A"), "short": True},
                    ],
                }
            ]
        }


class EmailTemplates:
    """Email templates."""

    @staticmethod
    def report_ready(data: Dict[str, Any]) -> Dict[str, str]:
        """Report ready email template."""
        period = data.get("period", "weekly")
        return {
            "subject": f"Your {period.capitalize()} Workout Report is Ready!",
            "body": f"""
Hello,

Your {period} workout report is ready to view!

View your detailed insights and progress analysis in the GymPT app.

Keep up the great work!

Best regards,
The GymPT Team
            """.strip(),
        }

    @staticmethod
    def recommendation_update(data: Dict[str, Any]) -> Dict[str, str]:
        """Recommendation update email template."""
        adjustment = data.get("adjustment", "MAINTAIN")
        reason = data.get("reason", "Based on your recent performance")

        return {
            "subject": f"Workout Intensity Update: {adjustment}",
            "body": f"""
Hello,

Your workout intensity recommendation has been updated to: {adjustment}

Reason: {reason}

Check the GymPT app for detailed recommendations.

Best regards,
The GymPT Team
            """.strip(),
        }

    @staticmethod
    def workout_completed(data: Dict[str, Any]) -> Dict[str, str]:
        """Workout completed email template."""
        score = data.get("score", "N/A")
        reps = data.get("reps", 0)

        return {
            "subject": "Great Job! Workout Completed",
            "body": f"""
Hello,

Congratulations on completing your workout!

Results:
- Form Score: {score}/10
- Reps Completed: {reps}

Keep up the excellent work!

Best regards,
The GymPT Team
            """.strip(),
        }

    @staticmethod
    def posture_alert(data: Dict[str, Any]) -> Dict[str, str]:
        """Posture alert email template."""
        issues = data.get("issues", [])
        issue_text = "\n- ".join(issues[:5]) if issues else "Form issues detected"

        return {
            "subject": "Form Alert - Review Your Technique",
            "body": f"""
Hello,

We detected some form issues during your workout:

- {issue_text}

Please review your technique and consider consulting with a trainer.

Best regards,
The GymPT Team
            """.strip(),
        }

    @staticmethod
    def goal_achieved(data: Dict[str, Any]) -> Dict[str, str]:
        """Goal achieved email template."""
        goal = data.get("goal", "workout goal")

        return {
            "subject": "Congratulations! Goal Achieved",
            "body": f"""
Hello,

Amazing news! You've achieved your {goal} goal!

This is a significant milestone in your fitness journey. Keep pushing forward!

Best regards,
The GymPT Team
            """.strip(),
        }

    @staticmethod
    def default(notification_type: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Default email template."""
        return {
            "subject": f"GymPT Notification: {notification_type}",
            "body": f"""
Hello,

You have a new notification from GymPT.

Type: {notification_type}

Please check the GymPT app for more details.

Best regards,
The GymPT Team
            """.strip(),
        }


class PushTemplates:
    """Push notification templates."""

    @staticmethod
    def report_ready(data: Dict[str, Any]) -> Dict[str, str]:
        """Report ready push template."""
        period = data.get("period", "weekly")
        return {
            "title": "Report Ready",
            "body": f"Your {period} workout report is ready! View insights.",
            "data": {"type": "REPORT_READY", "period": period},
        }

    @staticmethod
    def recommendation_update(data: Dict[str, Any]) -> Dict[str, str]:
        """Recommendation update push template."""
        adjustment = data.get("adjustment", "MAINTAIN")
        return {
            "title": "Intensity Update",
            "body": f"Workout intensity: {adjustment}",
            "data": {"type": "RECOMMENDATION_UPDATE", "adjustment": adjustment},
        }

    @staticmethod
    def workout_completed(data: Dict[str, Any]) -> Dict[str, str]:
        """Workout completed push template."""
        score = data.get("score", "N/A")
        return {
            "title": "Great Job!",
            "body": f"Workout completed! Form score: {score}/10",
            "data": {"type": "WORKOUT_COMPLETED", "score": score},
        }

    @staticmethod
    def posture_alert(data: Dict[str, Any]) -> Dict[str, str]:
        """Posture alert push template."""
        issues = data.get("issues", [])
        return {
            "title": "Form Alert",
            "body": f"{len(issues)} form issues detected. Review your technique.",
            "data": {"type": "POSTURE_ALERT", "issueCount": len(issues)},
        }

    @staticmethod
    def goal_achieved(data: Dict[str, Any]) -> Dict[str, str]:
        """Goal achieved push template."""
        goal = data.get("goal", "workout goal")
        return {
            "title": "Goal Achieved!",
            "body": f"Congratulations! You achieved your {goal} goal!",
            "data": {"type": "GOAL_ACHIEVED", "goal": goal},
        }

    @staticmethod
    def default(notification_type: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Default push template."""
        return {
            "title": "GymPT Notification",
            "body": notification_type,
            "data": {"type": notification_type},
        }
