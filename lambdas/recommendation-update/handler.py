import json
import logging
import os
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

import boto3
import requests
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
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "")
NOTIFICATION_QUEUE_URL = os.getenv("NOTIFICATION_QUEUE_URL", "")

# AWS clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
sqs_client = boto3.client("sqs", region_name=AWS_REGION)


def get_recent_workout_performance(user_id: str, limit: int = 5) -> Dict[str, Any]:
    """Get recent workout performance from DynamoDB."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-workout-sessions")

        response = table.query(
            KeyConditionExpression="userId = :uid",
            ExpressionAttributeValues={":uid": user_id},
            ScanIndexForward=False,
            Limit=limit,
        )

        sessions = response.get("Items", [])
        logger.info(f"Retrieved {len(sessions)} recent sessions for user: {user_id}")

        if not sessions:
            return {"averageScore": 0, "sessions": 0}

        # Calculate average score
        scores = [s.get("averageScore", 0) for s in sessions if "averageScore" in s]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Calculate completion rate
        completed = sum(1 for s in sessions if s.get("status") == "COMPLETED")
        completion_rate = completed / len(sessions) if sessions else 0

        return {
            "averageScore": round(avg_score, 2),
            "completionRate": round(completion_rate, 2),
            "sessions": len(sessions),
            "recentSessions": sessions,
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {"averageScore": 0, "sessions": 0}


def calculate_intensity_adjustment(performance: Dict[str, Any]) -> str:
    """
    Calculate recommended intensity adjustment based on performance.

    Returns: "INCREASE", "MAINTAIN", or "DECREASE"
    """
    avg_score = performance.get("averageScore", 0)
    completion_rate = performance.get("completionRate", 0)
    sessions = performance.get("sessions", 0)

    # Not enough data
    if sessions < 3:
        logger.info("Not enough sessions for adjustment")
        return "MAINTAIN"

    # Excellent performance - increase intensity
    if avg_score >= 8.5 and completion_rate >= 0.9:
        logger.info("Excellent performance - recommending intensity increase")
        return "INCREASE"

    # Poor performance - decrease intensity
    if avg_score < 6.0 or completion_rate < 0.5:
        logger.info("Poor performance - recommending intensity decrease")
        return "DECREASE"

    # Good performance - maintain
    logger.info("Good performance - maintaining intensity")
    return "MAINTAIN"


def generate_recommendation_update(user_id: str, adjustment: str, performance: Dict[str, Any]) -> Dict[str, Any]:
    """Generate recommendation update payload."""
    update = {
        "userId": user_id,
        "adjustment": adjustment,
        "performanceMetrics": {
            "averageScore": performance.get("averageScore"),
            "completionRate": performance.get("completionRate"),
            "totalSessions": performance.get("sessions"),
        },
        "updatedAt": datetime.utcnow().isoformat(),
    }

    # Add specific recommendations based on adjustment
    if adjustment == "INCREASE":
        update["recommendations"] = [
            "Increase weight by 5-10%",
            "Add 1-2 more reps per set",
            "Reduce rest time between sets",
        ]
    elif adjustment == "DECREASE":
        update["recommendations"] = [
            "Reduce weight by 10-15%",
            "Focus on form over intensity",
            "Increase rest time between sets",
            "Consider active recovery days",
        ]
    else:
        update["recommendations"] = [
            "Maintain current intensity",
            "Continue focusing on form",
        ]

    return update


def update_backend_api(recommendation: Dict[str, Any]) -> bool:
    """Send recommendation update to Backend API."""
    try:
        url = f"{BACKEND_API_URL}/api/v1/recommendations/update"

        headers = {
            "Content-Type": "application/json",
        }

        if BACKEND_API_KEY:
            headers["Authorization"] = f"Bearer {BACKEND_API_KEY}"

        response = requests.post(
            url,
            json=recommendation,
            headers=headers,
            timeout=10,
        )

        if response.status_code in (200, 201, 204):
            logger.info(f"Successfully updated backend API for user: {recommendation['userId']}")
            return True
        else:
            logger.error(f"Backend API error: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return False


def save_recommendation_history(recommendation: Dict[str, Any]) -> bool:
    """Save recommendation update to DynamoDB for history."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-recommendation-history")

        item = {
            "userId": recommendation["userId"],
            "timestamp": recommendation["updatedAt"],
            "adjustment": recommendation["adjustment"],
            "performanceMetrics": recommendation["performanceMetrics"],
            "recommendations": recommendation.get("recommendations", []),
        }

        table.put_item(Item=item)
        logger.info(f"Saved recommendation history for user: {recommendation['userId']}")
        return True
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return False


def send_recommendation_notification(recommendation: Dict[str, Any]):
    """Send RECOMMENDATION_UPDATE notification to notification queue."""
    if not NOTIFICATION_QUEUE_URL:
        logger.warning("NOTIFICATION_QUEUE_URL not configured, skipping notification")
        return

    try:
        message = {
            "type": "RECOMMENDATION_UPDATE",
            "userId": recommendation["userId"],
            "adjustment": recommendation["adjustment"],
            "recommendations": recommendation.get("recommendations", []),
            "performanceMetrics": recommendation.get("performanceMetrics", {}),
            "timestamp": datetime.utcnow().isoformat(),
        }

        sqs_client.send_message(
            QueueUrl=NOTIFICATION_QUEUE_URL,
            MessageBody=json.dumps(message),
        )

        logger.info(f"Sent recommendation notification for user: {recommendation['userId']}")
    except Exception as e:
        logger.error(f"Error sending recommendation notification: {e}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process workout completion events and update recommendations.

    Triggered by:
    - EventBridge rule on workout completion
    - SQS queue with workout session data

    Expected message format:
    {
        "userId": "user-uuid",
        "sessionId": "session-uuid",
        "completed": true
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        processed_count = 0
        failed_count = 0

        # Handle both direct invocation and SQS
        records = event.get("Records", [event])

        for record in records:
            try:
                # Parse message body if SQS
                if "body" in record:
                    message = json.loads(record["body"])
                else:
                    message = record

                user_id = message["userId"]
                session_id = message.get("sessionId")

                logger.info(f"Processing recommendation update for user: {user_id}")

                # Get recent performance
                performance = get_recent_workout_performance(user_id)

                # Calculate adjustment
                adjustment = calculate_intensity_adjustment(performance)

                # Generate recommendation
                recommendation = generate_recommendation_update(user_id, adjustment, performance)

                # Update backend API
                api_success = update_backend_api(recommendation)

                # Save to history
                history_success = save_recommendation_history(recommendation)

                if api_success or history_success:
                    processed_count += 1
                    logger.info(f"Updated recommendations for user: {user_id} - {adjustment}")
                    send_recommendation_notification(recommendation)
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error processing record: {e}", exc_info=True)
                failed_count += 1

        logger.info(f"Processed {processed_count} updates, {failed_count} failed")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "processed": processed_count,
                "failed": failed_count,
            }),
        }

    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
