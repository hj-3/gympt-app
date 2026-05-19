import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ["DYNAMODB_TABLE_PREFIX"] = "test"
os.environ["AWS_REGION"] = "ap-northeast-2"

from handler import (
    aggregate_issues,
    calculate_overall_score,
    enrich_event_data,
    lambda_handler,
    save_to_dynamodb,
)


def test_calculate_overall_score_no_issues():
    analysis = {"score": 9.0, "issues": []}
    score = calculate_overall_score(analysis)
    assert score == 9.0


def test_calculate_overall_score_with_medium_issues():
    analysis = {
        "score": 10.0,
        "issues": [
            {"type": "knee_valgus", "severity": "medium"},
            {"type": "depth", "severity": "medium"},
        ],
    }
    score = calculate_overall_score(analysis)
    assert score == 8.0  # 10 - 1 - 1


def test_calculate_overall_score_with_urgent_issues():
    analysis = {
        "score": 10.0,
        "issues": [
            {"type": "back_rounding", "severity": "urgent"},
        ],
    }
    score = calculate_overall_score(analysis)
    assert score == 7.0  # 10 - 3


def test_calculate_overall_score_floor():
    analysis = {
        "score": 2.0,
        "issues": [
            {"type": "issue1", "severity": "urgent"},
            {"type": "issue2", "severity": "urgent"},
        ],
    }
    score = calculate_overall_score(analysis)
    assert score == 0.0  # Floored at 0


def test_aggregate_issues():
    analysis = {
        "issues": [
            {"type": "knee_valgus", "severity": "medium"},
            {"type": "knee_valgus", "severity": "high"},
            {"type": "depth", "severity": "low"},
            {"type": "back_rounding", "severity": "urgent"},
        ]
    }

    result = aggregate_issues(analysis)

    assert result["totalIssues"] == 4
    assert result["typeBreakdown"]["knee_valgus"] == 2
    assert result["typeBreakdown"]["depth"] == 1
    assert result["severityBreakdown"]["medium"] == 1
    assert result["severityBreakdown"]["high"] == 1
    assert result["severityBreakdown"]["urgent"] == 1


def test_enrich_event_data():
    event_data = {
        "sessionId": "session-123",
        "userId": "user-123",
        "timestamp": "2024-05-18T10:00:00Z",
        "analysis": {
            "score": 8.0,
            "issues": [
                {"type": "knee_valgus", "severity": "medium"},
            ],
        },
    }

    enriched = enrich_event_data(event_data)

    assert "enrichedMetrics" in enriched
    assert enriched["enrichedMetrics"]["overallScore"] == 7.0  # 8 - 1
    assert enriched["enrichedMetrics"]["quality"] == "GOOD"
    assert enriched["enrichedMetrics"]["issueAggregation"]["totalIssues"] == 1


def test_enrich_event_data_excellent_quality():
    event_data = {
        "sessionId": "session-123",
        "analysis": {
            "score": 9.5,
            "issues": [],
        },
    }

    enriched = enrich_event_data(event_data)
    assert enriched["enrichedMetrics"]["quality"] == "EXCELLENT"


def test_enrich_event_data_poor_quality():
    event_data = {
        "sessionId": "session-123",
        "analysis": {
            "score": 4.0,
            "issues": [],
        },
    }

    enriched = enrich_event_data(event_data)
    assert enriched["enrichedMetrics"]["quality"] == "POOR"


@pytest.fixture
def mock_dynamodb_table():
    with patch("handler.dynamodb") as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_cloudwatch():
    with patch("handler.cloudwatch") as mock_cw:
        yield mock_cw


def test_save_to_dynamodb_success(mock_dynamodb_table):
    event_data = {
        "sessionId": "session-123",
        "userId": "user-123",
        "eventId": "evt-001",
        "timestamp": "2024-05-18T10:00:00Z",
        "analysis": {"score": 8.0},
        "enrichedMetrics": {"overallScore": 7.0},
        "processedAt": "2024-05-18T10:00:05Z",
    }

    result = save_to_dynamodb(event_data)

    assert result is True
    mock_dynamodb_table.put_item.assert_called_once()


def test_lambda_handler_success(mock_dynamodb_table, mock_cloudwatch):
    event = {
        "Records": [
            {
                "messageId": "msg-1",
                "body": json.dumps({
                    "sessionId": "session-123",
                    "userId": "user-123",
                    "eventId": "evt-001",
                    "timestamp": "2024-05-18T10:00:00Z",
                    "analysis": {
                        "score": 8.0,
                        "issues": [
                            {"type": "knee_valgus", "severity": "medium"}
                        ],
                    },
                }),
            }
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 1
    assert body["failed"] == 0

    mock_dynamodb_table.put_item.assert_called_once()
    mock_cloudwatch.put_metric_data.assert_called_once()


def test_lambda_handler_multiple_records(mock_dynamodb_table, mock_cloudwatch):
    event = {
        "Records": [
            {
                "messageId": "msg-1",
                "body": json.dumps({
                    "sessionId": "session-1",
                    "userId": "user-1",
                    "analysis": {"score": 8.0, "issues": []},
                }),
            },
            {
                "messageId": "msg-2",
                "body": json.dumps({
                    "sessionId": "session-2",
                    "userId": "user-2",
                    "analysis": {"score": 7.0, "issues": []},
                }),
            },
        ]
    }

    result = lambda_handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["processed"] == 2
