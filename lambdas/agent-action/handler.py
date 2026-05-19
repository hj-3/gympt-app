import json
import logging
import os
from datetime import datetime
from typing import Any, Dict
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
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# AWS clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get user profile from DynamoDB or Backend API."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-users")
        response = table.get_item(Key={"userId": user_id})

        if "Item" not in response:
            logger.warning(f"User not found: {user_id}")
            return {"error": "User not found"}

        item = response["Item"]
        logger.info(f"Retrieved user profile: {user_id}")

        return {
            "userId": item.get("userId"),
            "email": item.get("email"),
            "name": item.get("name"),
            "role": item.get("role", "USER"),
            "status": item.get("status", "ACTIVE"),
            "createdAt": item.get("createdAt"),
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {"error": str(e)}


def get_body_profile(user_id: str) -> Dict[str, Any]:
    """Get latest body profile for user."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-body-profiles")
        response = table.query(
            KeyConditionExpression="userId = :uid",
            ExpressionAttributeValues={":uid": user_id},
            ScanIndexForward=False,
            Limit=1,
        )

        if not response.get("Items"):
            logger.warning(f"No body profile found for user: {user_id}")
            return {"error": "Body profile not found"}

        item = response["Items"][0]
        logger.info(f"Retrieved body profile for user: {user_id}")

        return {
            "userId": item.get("userId"),
            "height": item.get("height"),
            "weight": item.get("weight"),
            "bmi": item.get("bmi"),
            "bodyFat": item.get("bodyFat"),
            "muscleMass": item.get("muscleMass"),
            "recordedAt": item.get("recordedAt"),
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {"error": str(e)}


def get_recent_workout_sessions(user_id: str, limit: int = 10) -> Dict[str, Any]:
    """Get recent workout sessions for user."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-workout-sessions")
        response = table.query(
            KeyConditionExpression="userId = :uid",
            ExpressionAttributeValues={":uid": user_id},
            ScanIndexForward=False,
            Limit=limit,
        )

        items = response.get("Items", [])
        logger.info(f"Retrieved {len(items)} workout sessions for user: {user_id}")

        return {
            "userId": user_id,
            "count": len(items),
            "sessions": [
                {
                    "sessionId": item.get("sessionId"),
                    "exerciseName": item.get("exerciseName"),
                    "duration": item.get("duration"),
                    "caloriesBurned": item.get("caloriesBurned"),
                    "averageScore": item.get("averageScore"),
                    "completedAt": item.get("completedAt"),
                }
                for item in items
            ],
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {"error": str(e)}


def save_workout_recommendation(user_id: str, recommendation: Dict[str, Any]) -> Dict[str, Any]:
    """Save workout recommendation to DynamoDB."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-recommendations")

        item = {
            "userId": user_id,
            "recommendationId": f"rec-{datetime.utcnow().isoformat()}",
            "workoutPlan": recommendation.get("workoutPlan"),
            "exercises": recommendation.get("exercises", []),
            "duration": recommendation.get("duration"),
            "intensity": recommendation.get("intensity"),
            "createdAt": datetime.utcnow().isoformat(),
            "status": "ACTIVE",
        }

        table.put_item(Item=item)
        logger.info(f"Saved workout recommendation for user: {user_id}")

        return {
            "success": True,
            "recommendationId": item["recommendationId"],
            "userId": user_id,
        }
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {"error": str(e)}


def get_posture_analysis_result(session_id: str) -> Dict[str, Any]:
    """Get posture analysis result for a workout session."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-posture-events")
        response = table.query(
            KeyConditionExpression="sessionId = :sid",
            ExpressionAttributeValues={":sid": session_id},
            ScanIndexForward=False,
            Limit=100,
        )

        items = response.get("Items", [])
        logger.info(f"Retrieved {len(items)} posture events for session: {session_id}")

        # Calculate aggregated metrics
        if items:
            scores = [item.get("score", 0) for item in items if "score" in item]
            avg_score = sum(scores) / len(scores) if scores else 0

            issues = []
            for item in items:
                if "issues" in item:
                    issues.extend(item["issues"])

            return {
                "sessionId": session_id,
                "eventCount": len(items),
                "averageScore": round(avg_score, 2),
                "totalIssues": len(issues),
                "issueBreakdown": _aggregate_issues(issues),
            }

        return {"sessionId": session_id, "eventCount": 0}
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return {"error": str(e)}


def create_workout_report(user_id: str, period: str = "weekly") -> Dict[str, Any]:
    """Create workout report for user."""
    try:
        # This would trigger report generation via SQS
        sqs = boto3.client("sqs", region_name=AWS_REGION)
        queue_url = os.getenv("REPORT_QUEUE_URL", "")

        if not queue_url:
            logger.warning("REPORT_QUEUE_URL not configured")
            return {"error": "Report queue not configured"}

        message = {
            "userId": user_id,
            "period": period,
            "requestedAt": datetime.utcnow().isoformat(),
        }

        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
        )

        logger.info(f"Queued report generation for user: {user_id}")

        return {
            "success": True,
            "userId": user_id,
            "period": period,
            "status": "QUEUED",
        }
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        return {"error": str(e)}


def _aggregate_issues(issues: list) -> Dict[str, int]:
    """Aggregate issues by type."""
    breakdown = {}
    for issue in issues:
        issue_type = issue.get("type", "unknown")
        breakdown[issue_type] = breakdown.get(issue_type, 0) + 1
    return breakdown


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Bedrock Agent Action Group handler.

    Expected event structure:
    {
        "actionGroup": "WorkoutActions",
        "function": "getUserProfile",
        "parameters": [
            {"name": "userId", "value": "uuid"}
        ]
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        action_group = event.get("actionGroup")
        function_name = event.get("function")
        parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}

        logger.info(f"Action: {action_group}/{function_name}, Params: {parameters}")

        # Route to appropriate function
        if function_name == "getUserProfile":
            result = get_user_profile(parameters.get("userId"))
        elif function_name == "getBodyProfile":
            result = get_body_profile(parameters.get("userId"))
        elif function_name == "getRecentWorkoutSessions":
            user_id = parameters.get("userId")
            limit = int(parameters.get("limit", 10))
            result = get_recent_workout_sessions(user_id, limit)
        elif function_name == "saveWorkoutRecommendation":
            user_id = parameters.get("userId")
            recommendation = json.loads(parameters.get("recommendation", "{}"))
            result = save_workout_recommendation(user_id, recommendation)
        elif function_name == "getPostureAnalysisResult":
            result = get_posture_analysis_result(parameters.get("sessionId"))
        elif function_name == "createWorkoutReport":
            user_id = parameters.get("userId")
            period = parameters.get("period", "weekly")
            result = create_workout_report(user_id, period)
        else:
            logger.error(f"Unknown function: {function_name}")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Unknown function: {function_name}"}),
            }

        # Return in Bedrock Agent format
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": action_group,
                "function": function_name,
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {"body": json.dumps(result)}
                    }
                }
            }
        }

    except Exception as e:
        logger.error(f"Error processing action: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
