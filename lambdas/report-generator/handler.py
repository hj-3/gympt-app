import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List
from pythonjsonlogger import jsonlogger

import boto3
from botocore.exceptions import ClientError

# Configure structured logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Environment variables
DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "gympt-local")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
S3_BUCKET = os.getenv("S3_BUCKET", "gympt-reports")
NOTIFICATION_QUEUE_URL = os.getenv("NOTIFICATION_QUEUE_URL", "")
ENABLE_BEDROCK_MOCK = os.getenv("ENABLE_BEDROCK_MOCK", "true").lower() == "true"
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")

# AWS clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)
sqs_client = boto3.client("sqs", region_name=AWS_REGION)

if not ENABLE_BEDROCK_MOCK:
    bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def get_workout_sessions(user_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Fetch workout sessions from DynamoDB for date range."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-workout-sessions")

        response = table.query(
            KeyConditionExpression="userId = :uid AND completedAt BETWEEN :start AND :end",
            ExpressionAttributeValues={
                ":uid": user_id,
                ":start": start_date,
                ":end": end_date,
            },
        )

        sessions = response.get("Items", [])
        logger.info(f"Retrieved {len(sessions)} workout sessions for user: {user_id}")
        return sessions
    except ClientError as e:
        logger.error(f"Error fetching workout sessions: {e}")
        return []


def get_posture_events(session_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch posture events for multiple sessions."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-posture-events")
        events_by_session = {}

        for session_id in session_ids:
            response = table.query(
                KeyConditionExpression="sessionId = :sid",
                ExpressionAttributeValues={":sid": session_id},
            )
            events_by_session[session_id] = response.get("Items", [])

        total_events = sum(len(events) for events in events_by_session.values())
        logger.info(f"Retrieved {total_events} posture events across {len(session_ids)} sessions")
        return events_by_session
    except ClientError as e:
        logger.error(f"Error fetching posture events: {e}")
        return {}


def calculate_metrics(sessions: List[Dict[str, Any]], posture_events: Dict[str, List]) -> Dict[str, Any]:
    """Calculate aggregate metrics from workout data."""
    if not sessions:
        return {
            "totalSessions": 0,
            "totalDuration": 0,
            "totalCalories": 0,
            "averageScore": 0,
        }

    total_duration = sum(s.get("duration", 0) for s in sessions)
    total_calories = sum(s.get("caloriesBurned", 0) for s in sessions)

    scores = []
    issue_counts = {}

    for session in sessions:
        session_id = session.get("sessionId")
        events = posture_events.get(session_id, [])

        for event in events:
            if "score" in event:
                scores.append(event["score"])

            for issue in event.get("issues", []):
                issue_type = issue.get("type", "unknown")
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

    avg_score = sum(scores) / len(scores) if scores else 0

    return {
        "totalSessions": len(sessions),
        "totalDuration": total_duration,
        "totalCalories": total_calories,
        "averageScore": round(avg_score, 2),
        "exerciseBreakdown": _aggregate_exercises(sessions),
        "commonIssues": sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5],
    }


def _aggregate_exercises(sessions: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count sessions by exercise type."""
    breakdown = {}
    for session in sessions:
        exercise = session.get("exerciseName", "Unknown")
        breakdown[exercise] = breakdown.get(exercise, 0) + 1
    return breakdown


def generate_report_with_bedrock(user_id: str, metrics: Dict[str, Any], period: str) -> str:
    """Generate report insights using Bedrock."""
    if ENABLE_BEDROCK_MOCK:
        logger.info("Using mock Bedrock response")
        return _generate_mock_report(metrics, period)

    try:
        prompt = f"""Analyze this workout data and provide actionable insights:

Period: {period}
Total Sessions: {metrics['totalSessions']}
Average Posture Score: {metrics['averageScore']}/10
Total Duration: {metrics['totalDuration']} seconds
Total Calories: {metrics['totalCalories']}
Common Issues: {', '.join([f"{issue[0]} ({issue[1]})" for issue in metrics['commonIssues'][:3]])}

Provide:
1. Performance summary
2. Key strengths
3. Areas for improvement
4. Specific recommendations

Keep the response concise and actionable."""

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        }

        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body),
        )

        response_body = json.loads(response["body"].read())
        insights = response_body["content"][0]["text"]

        logger.info("Generated report insights with Bedrock")
        return insights
    except Exception as e:
        logger.error(f"Bedrock error: {e}")
        return _generate_mock_report(metrics, period)


def _generate_mock_report(metrics: Dict[str, Any], period: str) -> str:
    """Generate mock report insights."""
    avg_score = metrics["averageScore"]

    if avg_score >= 8.0:
        performance = "Excellent! Your form consistency is outstanding."
        strengths = "Strong posture control across all exercises."
    elif avg_score >= 6.0:
        performance = "Good progress with room for refinement."
        strengths = "Consistent workout frequency and effort."
    else:
        performance = "Focus needed on form fundamentals."
        strengths = "Showing up regularly is the first step."

    recommendations = []
    for issue, count in metrics["commonIssues"][:3]:
        if issue == "knee_valgus":
            recommendations.append("- Practice glute activation exercises to strengthen hip abductors")
        elif issue == "depth":
            recommendations.append("- Work on ankle mobility to achieve proper squat depth")
        elif issue == "back_rounding":
            recommendations.append("- Strengthen core and practice bracing techniques")
        elif issue == "elbow_flare":
            recommendations.append("- Focus on keeping elbows tucked at 45 degrees")

    return f"""**Performance Summary:**
{performance} You completed {metrics['totalSessions']} sessions this {period}, burning {metrics['totalCalories']} calories.

**Key Strengths:**
{strengths}

**Areas for Improvement:**
Your most common form issues were: {', '.join([issue[0] for issue in metrics['commonIssues'][:3]])}

**Recommendations:**
{chr(10).join(recommendations) if recommendations else '- Continue maintaining your current routine'}
"""


def save_report_to_s3(user_id: str, report_data: Dict[str, Any]) -> str:
    """Save report JSON to S3."""
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        key = f"reports/{user_id}/{timestamp}_report.json"

        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(report_data, indent=2),
            ContentType="application/json",
        )

        logger.info(f"Saved report to S3: s3://{S3_BUCKET}/{key}")
        return f"s3://{S3_BUCKET}/{key}"
    except ClientError as e:
        logger.error(f"Error saving to S3: {e}")
        raise


def send_notification(user_id: str, report_url: str, period: str):
    """Send notification via SQS."""
    if not NOTIFICATION_QUEUE_URL:
        logger.warning("NOTIFICATION_QUEUE_URL not configured, skipping notification")
        return

    try:
        message = {
            "type": "REPORT_READY",
            "userId": user_id,
            "reportUrl": report_url,
            "period": period,
            "timestamp": datetime.utcnow().isoformat(),
        }

        sqs_client.send_message(
            QueueUrl=NOTIFICATION_QUEUE_URL,
            MessageBody=json.dumps(message),
        )

        logger.info(f"Sent notification for user: {user_id}")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process report generation requests from SQS.

    Expected message format:
    {
        "userId": "uuid",
        "period": "weekly|monthly",
        "requestedAt": "ISO timestamp"
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Parse SQS records
        for record in event.get("Records", []):
            message_body = json.loads(record["body"])

            user_id = message_body["userId"]
            period = message_body.get("period", "weekly")

            logger.info(f"Generating {period} report for user: {user_id}")

            # Calculate date range
            end_date = datetime.utcnow()
            if period == "weekly":
                start_date = end_date - timedelta(days=7)
            elif period == "monthly":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)

            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat()

            # Fetch data
            sessions = get_workout_sessions(user_id, start_date_str, end_date_str)

            if not sessions:
                logger.warning(f"No workout sessions found for user: {user_id}")
                continue

            session_ids = [s["sessionId"] for s in sessions]
            posture_events = get_posture_events(session_ids)

            # Calculate metrics
            metrics = calculate_metrics(sessions, posture_events)

            # Generate insights
            insights = generate_report_with_bedrock(user_id, metrics, period)

            # Create report
            report_data = {
                "userId": user_id,
                "period": period,
                "startDate": start_date_str,
                "endDate": end_date_str,
                "metrics": metrics,
                "insights": insights,
                "generatedAt": datetime.utcnow().isoformat(),
            }

            # Save to S3
            report_url = save_report_to_s3(user_id, report_data)

            # Send notification
            send_notification(user_id, report_url, period)

            logger.info(f"Successfully generated report for user: {user_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Reports generated successfully"}),
        }

    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
