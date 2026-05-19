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

# AWS clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)


def validate_wearable_data(data: Dict[str, Any]) -> bool:
    """Validate wearable data structure."""
    required_fields = ["userId", "deviceType", "timestamp", "metrics"]

    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field: {field}")
            return False

    # Validate metrics
    metrics = data.get("metrics", {})
    if not isinstance(metrics, dict):
        logger.error("Metrics must be a dictionary")
        return False

    return True


def normalize_metrics(metrics: Dict[str, Any], device_type: str) -> Dict[str, Any]:
    """
    Normalize metrics from different wearable devices.

    Supports:
    - Apple Watch (heartRate, steps, calories, activeMinutes)
    - Fitbit (heart_rate, steps, calories_burned, active_minutes)
    - Garmin (hr, step_count, kcal, active_time_minutes)
    """
    normalized = {}

    # Heart rate normalization
    if "heartRate" in metrics:
        normalized["heartRate"] = metrics["heartRate"]
    elif "heart_rate" in metrics:
        normalized["heartRate"] = metrics["heart_rate"]
    elif "hr" in metrics:
        normalized["heartRate"] = metrics["hr"]

    # Steps normalization
    if "steps" in metrics:
        normalized["steps"] = metrics["steps"]
    elif "step_count" in metrics:
        normalized["steps"] = metrics["step_count"]

    # Calories normalization
    if "calories" in metrics:
        normalized["calories"] = metrics["calories"]
    elif "calories_burned" in metrics:
        normalized["calories"] = metrics["calories_burned"]
    elif "kcal" in metrics:
        normalized["calories"] = metrics["kcal"]

    # Active minutes normalization
    if "activeMinutes" in metrics:
        normalized["activeMinutes"] = metrics["activeMinutes"]
    elif "active_minutes" in metrics:
        normalized["activeMinutes"] = metrics["active_minutes"]
    elif "active_time_minutes" in metrics:
        normalized["activeMinutes"] = metrics["active_time_minutes"]

    # Distance (optional)
    if "distance" in metrics:
        normalized["distance"] = metrics["distance"]
    elif "distance_meters" in metrics:
        normalized["distance"] = metrics["distance_meters"] / 1000  # Convert to km

    # Sleep data (optional)
    if "sleepMinutes" in metrics:
        normalized["sleepMinutes"] = metrics["sleepMinutes"]
    elif "sleep_minutes" in metrics:
        normalized["sleepMinutes"] = metrics["sleep_minutes"]

    logger.info(f"Normalized {len(normalized)} metrics from {device_type}")
    return normalized


def save_wearable_event(event_data: Dict[str, Any]) -> bool:
    """Save wearable event to DynamoDB."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-wearable-events")

        item = {
            "userId": event_data["userId"],
            "timestamp": event_data["timestamp"],
            "eventId": f"wearable-{datetime.utcnow().isoformat()}",
            "deviceType": event_data["deviceType"],
            "deviceId": event_data.get("deviceId", "unknown"),
            "metrics": event_data["normalizedMetrics"],
            "rawMetrics": event_data.get("metrics"),
            "syncedAt": datetime.utcnow().isoformat(),
        }

        table.put_item(Item=item)
        logger.info(f"Saved wearable event for user: {event_data['userId']}")
        return True
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return False


def calculate_daily_aggregates(user_id: str, date: str) -> Dict[str, Any]:
    """
    Calculate daily aggregate metrics for a user.

    This would query all wearable events for a given date
    and compute totals/averages.
    """
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-wearable-events")

        # Query events for the day
        start_timestamp = f"{date}T00:00:00Z"
        end_timestamp = f"{date}T23:59:59Z"

        response = table.query(
            KeyConditionExpression="userId = :uid AND #ts BETWEEN :start AND :end",
            ExpressionAttributeNames={"#ts": "timestamp"},
            ExpressionAttributeValues={
                ":uid": user_id,
                ":start": start_timestamp,
                ":end": end_timestamp,
            },
        )

        events = response.get("Items", [])

        if not events:
            return {"date": date, "totalEvents": 0}

        # Aggregate metrics
        total_steps = 0
        total_calories = 0
        total_active_minutes = 0
        heart_rates = []

        for event in events:
            metrics = event.get("metrics", {})
            if "steps" in metrics:
                total_steps += metrics["steps"]
            if "calories" in metrics:
                total_calories += metrics["calories"]
            if "activeMinutes" in metrics:
                total_active_minutes += metrics["activeMinutes"]
            if "heartRate" in metrics:
                heart_rates.append(metrics["heartRate"])

        avg_heart_rate = sum(heart_rates) / len(heart_rates) if heart_rates else 0

        return {
            "date": date,
            "totalEvents": len(events),
            "totalSteps": total_steps,
            "totalCalories": total_calories,
            "totalActiveMinutes": total_active_minutes,
            "averageHeartRate": round(avg_heart_rate, 1),
        }
    except ClientError as e:
        logger.error(f"Error calculating aggregates: {e}")
        return {"error": str(e)}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process wearable sync events from SQS.

    Expected message format:
    {
        "userId": "user-uuid",
        "deviceType": "apple_watch|fitbit|garmin",
        "deviceId": "device-id",
        "timestamp": "ISO timestamp",
        "metrics": {
            "heartRate": 75,
            "steps": 1000,
            "calories": 50,
            "activeMinutes": 10
        }
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        processed_count = 0
        failed_count = 0

        # Process each SQS record
        for record in event.get("Records", []):
            try:
                message_body = json.loads(record["body"])

                # Validate data
                if not validate_wearable_data(message_body):
                    logger.error("Invalid wearable data")
                    failed_count += 1
                    continue

                # Normalize metrics
                device_type = message_body["deviceType"]
                raw_metrics = message_body["metrics"]
                normalized_metrics = normalize_metrics(raw_metrics, device_type)

                # Prepare event data
                event_data = {
                    **message_body,
                    "normalizedMetrics": normalized_metrics,
                }

                # Save to DynamoDB
                if save_wearable_event(event_data):
                    processed_count += 1

                    # Calculate daily aggregates (optional, can be async)
                    date = message_body["timestamp"][:10]  # Extract YYYY-MM-DD
                    aggregates = calculate_daily_aggregates(message_body["userId"], date)
                    logger.info(f"Daily aggregates: {aggregates}")
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error processing record: {e}", exc_info=True)
                failed_count += 1

        logger.info(f"Processed {processed_count} events, {failed_count} failed")

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
