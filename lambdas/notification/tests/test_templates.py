"""Tests for notification templates."""

import pytest
from templates import (
    NotificationTemplate,
    SlackTemplates,
    EmailTemplates,
    PushTemplates,
)


class TestSlackTemplates:
    """Test Slack message templates."""

    def test_report_ready_template(self):
        """Test report ready Slack template."""
        data = {
            "userId": "user-123",
            "period": "weekly",
            "reportUrl": "s3://bucket/report.json",
        }

        result = SlackTemplates.report_ready(data)

        assert "attachments" in result
        assert result["attachments"][0]["color"] == "#36a64f"
        assert "Weekly" in result["attachments"][0]["title"]
        assert len(result["attachments"][0]["fields"]) == 2

    def test_recommendation_update_increase(self):
        """Test recommendation update template for increase."""
        data = {
            "userId": "user-123",
            "adjustment": "INCREASE",
            "reason": "Excellent performance",
        }

        result = SlackTemplates.recommendation_update(data)

        assert "attachments" in result
        assert "📈" in result["attachments"][0]["title"]
        assert "INCREASE" in result["attachments"][0]["title"]
        assert result["attachments"][0]["color"] == "#36a64f"

    def test_recommendation_update_decrease(self):
        """Test recommendation update template for decrease."""
        data = {
            "userId": "user-123",
            "adjustment": "DECREASE",
            "reason": "Form needs improvement",
        }

        result = SlackTemplates.recommendation_update(data)

        assert "📉" in result["attachments"][0]["title"]
        assert result["attachments"][0]["color"] == "#ff9800"

    def test_workout_completed_template(self):
        """Test workout completed Slack template."""
        data = {
            "userId": "user-123",
            "score": 8.5,
            "reps": 50,
        }

        result = SlackTemplates.workout_completed(data)

        assert "Great Job" in result["attachments"][0]["title"]
        assert "8.5" in result["attachments"][0]["text"]
        assert "50" in result["attachments"][0]["text"]

    def test_posture_alert_template(self):
        """Test posture alert Slack template."""
        data = {
            "userId": "user-123",
            "sessionId": "session-456",
            "issues": ["knee_valgus", "depth", "back_rounding"],
        }

        result = SlackTemplates.posture_alert(data)

        assert "Form Alert" in result["attachments"][0]["title"]
        assert result["attachments"][0]["color"] == "#ff5722"
        assert "3" in str(result["attachments"][0]["fields"])

    def test_goal_achieved_template(self):
        """Test goal achieved Slack template."""
        data = {
            "userId": "user-123",
            "goal": "100 workouts",
        }

        result = SlackTemplates.goal_achieved(data)

        assert "Congratulations" in result["attachments"][0]["title"]
        assert "100 workouts" in result["attachments"][0]["text"]

    def test_default_template(self):
        """Test default Slack template."""
        data = {"userId": "user-123"}

        result = SlackTemplates.default("CUSTOM_TYPE", data)

        assert "text" in result
        assert "CUSTOM_TYPE" in result["text"]


class TestEmailTemplates:
    """Test email templates."""

    def test_report_ready_email(self):
        """Test report ready email template."""
        data = {
            "userId": "user-123",
            "period": "monthly",
        }

        result = EmailTemplates.report_ready(data)

        assert "subject" in result
        assert "body" in result
        assert "Monthly" in result["subject"]
        assert "monthly" in result["body"]
        assert "GymPT" in result["body"]

    def test_recommendation_update_email(self):
        """Test recommendation update email template."""
        data = {
            "userId": "user-123",
            "adjustment": "INCREASE",
            "reason": "Strong performance metrics",
        }

        result = EmailTemplates.recommendation_update(data)

        assert "INCREASE" in result["subject"]
        assert "INCREASE" in result["body"]
        assert "Strong performance metrics" in result["body"]

    def test_workout_completed_email(self):
        """Test workout completed email template."""
        data = {
            "userId": "user-123",
            "score": 9.0,
            "reps": 60,
        }

        result = EmailTemplates.workout_completed(data)

        assert "Workout Completed" in result["subject"]
        assert "9.0" in result["body"]
        assert "60" in result["body"]

    def test_posture_alert_email(self):
        """Test posture alert email template."""
        data = {
            "userId": "user-123",
            "issues": ["knee_valgus", "depth", "elbow_flare"],
        }

        result = EmailTemplates.posture_alert(data)

        assert "Form Alert" in result["subject"]
        assert "knee_valgus" in result["body"]
        assert "depth" in result["body"]
        assert "elbow_flare" in result["body"]

    def test_goal_achieved_email(self):
        """Test goal achieved email template."""
        data = {
            "userId": "user-123",
            "goal": "50 consecutive days",
        }

        result = EmailTemplates.goal_achieved(data)

        assert "Congratulations" in result["subject"]
        assert "50 consecutive days" in result["body"]

    def test_default_email(self):
        """Test default email template."""
        data = {"userId": "user-123"}

        result = EmailTemplates.default("CUSTOM_NOTIFICATION", data)

        assert "GymPT Notification" in result["subject"]
        assert "CUSTOM_NOTIFICATION" in result["body"]


class TestPushTemplates:
    """Test push notification templates."""

    def test_report_ready_push(self):
        """Test report ready push template."""
        data = {
            "userId": "user-123",
            "period": "weekly",
        }

        result = PushTemplates.report_ready(data)

        assert "title" in result
        assert "body" in result
        assert "data" in result
        assert "Report Ready" == result["title"]
        assert "weekly" in result["body"]
        assert result["data"]["type"] == "REPORT_READY"
        assert result["data"]["period"] == "weekly"

    def test_recommendation_update_push(self):
        """Test recommendation update push template."""
        data = {
            "userId": "user-123",
            "adjustment": "MAINTAIN",
        }

        result = PushTemplates.recommendation_update(data)

        assert "Intensity Update" == result["title"]
        assert "MAINTAIN" in result["body"]
        assert result["data"]["adjustment"] == "MAINTAIN"

    def test_workout_completed_push(self):
        """Test workout completed push template."""
        data = {
            "userId": "user-123",
            "score": 8.0,
        }

        result = PushTemplates.workout_completed(data)

        assert "Great Job" in result["title"]
        assert "8.0" in result["body"]
        assert result["data"]["score"] == 8.0

    def test_posture_alert_push(self):
        """Test posture alert push template."""
        data = {
            "userId": "user-123",
            "issues": ["knee_valgus", "depth"],
        }

        result = PushTemplates.posture_alert(data)

        assert "Form Alert" == result["title"]
        assert "2" in result["body"]
        assert result["data"]["issueCount"] == 2

    def test_goal_achieved_push(self):
        """Test goal achieved push template."""
        data = {
            "userId": "user-123",
            "goal": "personal record",
        }

        result = PushTemplates.goal_achieved(data)

        assert "Goal Achieved" in result["title"]
        assert "personal record" in result["body"]
        assert result["data"]["goal"] == "personal record"


class TestNotificationTemplate:
    """Test notification template wrapper."""

    def test_render_slack_report_ready(self):
        """Test rendering Slack template."""
        data = {"userId": "user-123", "period": "weekly"}

        result = NotificationTemplate.render_slack("REPORT_READY", data)

        assert "attachments" in result
        assert "Weekly" in result["attachments"][0]["title"]

    def test_render_email_workout_completed(self):
        """Test rendering email template."""
        data = {"userId": "user-123", "score": 9.0, "reps": 60}

        result = NotificationTemplate.render_email("WORKOUT_COMPLETED", data)

        assert "subject" in result
        assert "body" in result
        assert "Workout Completed" in result["subject"]

    def test_render_push_goal_achieved(self):
        """Test rendering push template."""
        data = {"userId": "user-123", "goal": "milestone"}

        result = NotificationTemplate.render_push("GOAL_ACHIEVED", data)

        assert "title" in result
        assert "body" in result
        assert "data" in result

    def test_render_unknown_type_slack(self):
        """Test rendering unknown type falls back to default."""
        data = {"userId": "user-123"}

        result = NotificationTemplate.render_slack("UNKNOWN_TYPE", data)

        assert "text" in result or "attachments" in result

    def test_render_all_channels(self):
        """Test rendering same notification across all channels."""
        data = {
            "userId": "user-123",
            "adjustment": "INCREASE",
            "reason": "Great progress",
        }

        slack_result = NotificationTemplate.render_slack("RECOMMENDATION_UPDATE", data)
        email_result = NotificationTemplate.render_email("RECOMMENDATION_UPDATE", data)
        push_result = NotificationTemplate.render_push("RECOMMENDATION_UPDATE", data)

        # All should contain key information
        assert "INCREASE" in str(slack_result)
        assert "INCREASE" in email_result["subject"]
        assert "INCREASE" in push_result["body"]


class TestTemplateConsistency:
    """Test consistency across templates."""

    def test_all_notification_types_have_templates(self):
        """Test that all notification types have templates for each channel."""
        notification_types = [
            "REPORT_READY",
            "RECOMMENDATION_UPDATE",
            "WORKOUT_COMPLETED",
            "POSTURE_ALERT",
            "GOAL_ACHIEVED",
        ]

        for notification_type in notification_types:
            data = {"userId": "test-user"}

            # Should not raise exceptions
            slack = NotificationTemplate.render_slack(notification_type, data)
            email = NotificationTemplate.render_email(notification_type, data)
            push = NotificationTemplate.render_push(notification_type, data)

            assert slack is not None
            assert email is not None
            assert push is not None

    def test_required_fields_in_all_templates(self):
        """Test that all templates have required fields."""
        data = {"userId": "user-123"}

        # Slack should have attachments or text
        slack = NotificationTemplate.render_slack("REPORT_READY", data)
        assert "attachments" in slack or "text" in slack

        # Email should have subject and body
        email = NotificationTemplate.render_email("REPORT_READY", data)
        assert "subject" in email
        assert "body" in email

        # Push should have title, body, and data
        push = NotificationTemplate.render_push("REPORT_READY", data)
        assert "title" in push
        assert "body" in push
        assert "data" in push
