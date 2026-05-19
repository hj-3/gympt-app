import json
import logging
import os
from datetime import datetime
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
CLOUDWATCH_NAMESPACE = os.getenv("CLOUDWATCH_NAMESPACE", "GymPT/PostureAnalysis")

# AWS clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
cloudwatch = boto3.client("cloudwatch", region_name=AWS_REGION)


def calculate_overall_score(analysis: Dict[str, Any]) -> float:
    """Calculate overall score from analysis data."""
    base_score = analysis.get("score", 10.0)

    # Adjust based on issue severity
    severity_penalties = {
        "urgent": 3.0,
        "high": 2.0,
        "medium": 1.0,
        "low": 0.5,
    }

    for issue in analysis.get("issues", []):
        severity = issue.get("severity", "low")
        penalty = severity_penalties.get(severity, 0.5)
        base_score -= penalty

    return max(0.0, min(10.0, base_score))


def aggregate_issues(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate issues by type and severity."""
    issues = analysis.get("issues", [])

    type_counts = {}
    severity_counts = {"urgent": 0, "high": 0, "medium": 0, "low": 0}

    for issue in issues:
        issue_type = issue.get("type", "unknown")
        severity = issue.get("severity", "low")

        type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "typeBreakdown": type_counts,
        "severityBreakdown": severity_counts,
        "totalIssues": len(issues),
    }


def enrich_event_data(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich posture event with calculated metrics."""
    analysis = event_data.get("analysis", {})

    # Calculate scores
    overall_score = calculate_overall_score(analysis)
    issue_aggregation = aggregate_issues(analysis)

    # Determine quality rating
    if overall_score >= 9.0:
        quality = "EXCELLENT"
    elif overall_score >= 7.0:
        quality = "GOOD"
    elif overall_score >= 5.0:
        quality = "FAIR"
    else:
        quality = "POOR"

    enriched = {
        **event_data,
        "enrichedMetrics": {
            "overallScore": round(overall_score, 2),
            "quality": quality,
            "issueAggregation": issue_aggregation,
        },
        "processedAt": datetime.utcnow().isoformat(),
    }

    return enriched


def save_to_dynamodb(event_data: Dict[str, Any]) -> bool:
    """Save enriched event to DynamoDB."""
    try:
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-posture-events")

        item = {
            "sessionId": event_data["sessionId"],
            "eventId": event_data.get("eventId", f"evt-{datetime.utcnow().isoformat()}"),
            "userId": event_data.get("userId"),
            "timestamp": event_data.get("timestamp"),
            "analysis": event_data.get("analysis"),
            "enrichedMetrics": event_data.get("enrichedMetrics"),
            "processedAt": event_data.get("processedAt"),
        }

        table.put_item(Item=item)
        logger.info(f"Saved posture event to DynamoDB: {item['eventId']}")
        return True
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return False


def publish_cloudwatch_metrics(event_data: Dict[str, Any]):
    """Publish custom metrics to CloudWatch."""
    try:
        metrics = event_data.get("enrichedMetrics", {})
        session_id = event_data.get("sessionId")
        user_id = event_data.get("userId")

        metric_data = [
            {
                "MetricName": "PostureScore",
                "Value": metrics.get("overallScore", 0),
                "Unit": "None",
                "Dimensions": [
                    {"Name": "SessionId", "Value": session_id},
                    {"Name": "UserId", "Value": user_id},
                ],
            },
            {
                "MetricName": "IssueCount",
                "Value": metrics.get("issueAggregation", {}).get("totalIssues", 0),
                "Unit": "Count",
                "Dimensions": [
                    {"Name": "SessionId", "Value": session_id},
                ],
            },
        ]

        # Add severity-specific metrics
        severity_breakdown = metrics.get("issueAggregation", {}).get("severityBreakdown", {})
        for severity, count in severity_breakdown.items():
            if count > 0:
                metric_data.append({
                    "MetricName": f"Issues_{severity.capitalize()}",
                    "Value": count,
                    "Unit": "Count",
                    "Dimensions": [
                        {"Name": "SessionId", "Value": session_id},
                        {"Name": "Severity", "Value": severity},
                    ],
                })

        cloudwatch.put_metric_data(
            Namespace=CLOUDWATCH_NAMESPACE,
            MetricData=metric_data,
        )

        logger.info(f"Published {len(metric_data)} CloudWatch metrics")
    except Exception as e:
        logger.error(f"CloudWatch error: {e}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process posture events from SQS.

    Expected message format:
    {
        "sessionId": "session-uuid",
        "userId": "user-uuid",
        "eventId": "event-uuid",
        "timestamp": "ISO timestamp",
        "analysis": {
            "score": 8.0,
            "issues": [
                {
                    "type": "knee_valgus",
                    "severity": "medium",
                    "correction": "Push knees outward"
                }
            ]
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

                # Enrich event data
                enriched_event = enrich_event_data(message_body)

                # Save to DynamoDB
                if save_to_dynamodb(enriched_event):
                    # Publish CloudWatch metrics
                    publish_cloudwatch_metrics(enriched_event)
                    processed_count += 1
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
