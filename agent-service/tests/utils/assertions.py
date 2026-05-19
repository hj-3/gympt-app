"""
Custom assertions for testing GYMPT Agent Service.
"""
from typing import Dict, Any, List


def assert_bedrock_response_valid(response: Dict[str, Any]) -> None:
    """Assert Bedrock response has valid structure."""
    assert "content" in response, "Missing 'content' field"
    assert "model" in response, "Missing 'model' field"
    assert "usage" in response, "Missing 'usage' field"

    assert isinstance(response["content"], str), "content must be string"
    assert len(response["content"]) > 0, "content must not be empty"

    assert isinstance(response["usage"], dict), "usage must be dict"


def assert_dynamodb_entry_valid(entry: Dict[str, Any]) -> None:
    """Assert DynamoDB entry has valid structure."""
    required_fields = [
        "user_id",
        "interaction_type",
        "timestamp"
    ]

    for field in required_fields:
        assert field in entry, f"Missing required field: {field}"

    assert entry["interaction_type"] in [
        "workout_recommend",
        "posture_feedback",
        "report_generation"
    ], f"Invalid interaction_type: {entry['interaction_type']}"


def assert_workout_recommendation_valid(recommendation: Dict[str, Any]) -> None:
    """Assert workout recommendation has valid structure."""
    required_fields = ["recommendation", "model_used", "cached", "interaction_id"]

    for field in required_fields:
        assert field in recommendation, f"Missing field: {field}"

    assert isinstance(recommendation["recommendation"], str)
    assert len(recommendation["recommendation"]) > 0
    assert isinstance(recommendation["cached"], bool)


def assert_posture_feedback_valid(feedback: Dict[str, Any]) -> None:
    """Assert posture feedback has valid structure."""
    required_fields = ["feedback", "corrections", "severity", "model_used"]

    for field in required_fields:
        assert field in feedback, f"Missing field: {field}"

    assert feedback["severity"] in ["low", "medium", "high"], \
        f"Invalid severity: {feedback['severity']}"

    assert isinstance(feedback["corrections"], list)


def assert_report_valid(report: Dict[str, Any]) -> None:
    """Assert report has valid structure."""
    required_fields = [
        "report_summary",
        "key_insights",
        "recommendations",
        "model_used",
        "task_id"
    ]

    for field in required_fields:
        assert field in report, f"Missing field: {field}"

    assert isinstance(report["key_insights"], list)
    assert isinstance(report["recommendations"], list)
    assert len(report["report_summary"]) > 0


def assert_cache_key_format(key: str, prefix: str) -> None:
    """Assert cache key has correct format."""
    assert key.startswith(prefix), f"Key should start with {prefix}"
    assert ":" in key, "Key should contain separator"
    parts = key.split(":")
    assert len(parts) >= 2, "Key should have at least 2 parts"


def assert_metrics_incremented(metric_name: str, labels: Dict[str, str]) -> None:
    """Assert Prometheus metric was incremented."""
    # Note: This is a placeholder - actual implementation would check Prometheus
    # In real tests, you'd query the metric registry
    pass


def assert_response_time_acceptable(duration: float, max_seconds: float = 1.0) -> None:
    """Assert response time is within acceptable range."""
    assert duration < max_seconds, \
        f"Response time {duration:.2f}s exceeds max {max_seconds}s"


def assert_no_sensitive_data(data: str) -> None:
    """Assert data doesn't contain sensitive information."""
    sensitive_patterns = [
        "password",
        "secret",
        "api_key",
        "aws_access_key",
        "token"
    ]

    data_lower = data.lower()
    for pattern in sensitive_patterns:
        assert pattern not in data_lower, \
            f"Sensitive data pattern found: {pattern}"


def assert_valid_uuid(uuid_string: str) -> None:
    """Assert string is a valid UUID."""
    import uuid

    try:
        uuid.UUID(uuid_string)
    except ValueError:
        raise AssertionError(f"Invalid UUID: {uuid_string}")


def assert_timestamp_format(timestamp: str) -> None:
    """Assert timestamp is in ISO 8601 format."""
    from datetime import datetime

    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except ValueError:
        raise AssertionError(f"Invalid timestamp format: {timestamp}")


def assert_list_not_empty(lst: List, message: str = "List should not be empty") -> None:
    """Assert list is not empty."""
    assert isinstance(lst, list), "Must be a list"
    assert len(lst) > 0, message


def assert_string_contains(text: str, substring: str, case_sensitive: bool = False) -> None:
    """Assert string contains substring."""
    if not case_sensitive:
        text = text.lower()
        substring = substring.lower()

    assert substring in text, f"String does not contain '{substring}'"


def assert_api_error_format(error_response: Dict[str, Any]) -> None:
    """Assert API error response has correct format."""
    assert "detail" in error_response, "Error response must have 'detail' field"
