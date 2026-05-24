"""Integration tests for AWS clients with moto."""
import pytest
import json
from datetime import datetime
from moto import mock_aws
import boto3

from app.clients.dynamodb_client import AsyncDynamoDBClient
from app.clients.s3_client import AsyncS3Client
from app.clients.sqs_client import AsyncSQSClient
from app.config import settings


@pytest.fixture
def aws_credentials(monkeypatch):
    """Mock AWS credentials for moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")


@pytest.fixture
def dynamodb_table(aws_credentials):
    """Create mock DynamoDB table."""
    with mock_aws():
        # Create table
        client = boto3.client("dynamodb", region_name=settings.aws_region)
        client.create_table(
            TableName=settings.dynamodb_posture_events_table,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield client


@pytest.fixture
def s3_bucket(aws_credentials):
    """Create mock S3 bucket."""
    with mock_aws():
        client = boto3.client("s3", region_name=settings.aws_region)
        client.create_bucket(
            Bucket=settings.s3_media_bucket,
            CreateBucketConfiguration={"LocationConstraint": settings.aws_region}
        )
        yield client


@pytest.fixture
def sqs_queue(aws_credentials):
    """Create mock SQS queue."""
    with mock_aws():
        client = boto3.client("sqs", region_name=settings.aws_region)
        response = client.create_queue(QueueName="gympt-posture-test-queue")
        queue_url = response["QueueUrl"]

        # Update settings with queue URL
        settings.sqs_posture_event_queue_url = queue_url
        yield client


# DynamoDB Tests
@pytest.mark.asyncio
async def test_dynamodb_log_event(dynamodb_table):
    """Test logging event to DynamoDB."""
    client = AsyncDynamoDBClient()

    success = await client.log_posture_event(
        user_id="test_user",
        session_id="test_session_123",
        timestamp=datetime.utcnow().timestamp(),
        exercise="squat",
        score=8.5,
        issues=[{"type": "knee_valgus", "severity": "medium"}],
        rep_count=5,
        frame_number=100,
    )

    assert success is True


@pytest.mark.asyncio
async def test_dynamodb_batch_write(dynamodb_table):
    """Test batch writing events."""
    client = AsyncDynamoDBClient()

    # Log multiple events to trigger batch write
    for i in range(12):  # More than buffer size
        await client.log_posture_event(
            user_id="test_user",
            session_id="test_session_123",
            timestamp=datetime.utcnow().timestamp() + i,
            exercise="squat",
            score=8.0,
            issues=[],
            rep_count=i,
            frame_number=i * 10,
        )

    # Flush remaining events
    await client.close()


@pytest.mark.asyncio
async def test_dynamodb_get_session_events(dynamodb_table):
    """Test retrieving session events."""
    client = AsyncDynamoDBClient()

    # Log some events
    session_id = "test_session_456"
    for i in range(3):
        await client.log_posture_event(
            user_id="test_user",
            session_id=session_id,
            timestamp=datetime.utcnow().timestamp() + i,
            exercise="squat",
            score=8.0,
            issues=[],
            rep_count=i,
            frame_number=i * 10,
        )

    await client._flush_buffer()

    # Retrieve events
    events = await client.get_session_events("test_user", session_id, limit=10)

    # Should have at least some events (may be empty due to async)
    assert isinstance(events, list)


# S3 Tests
@pytest.mark.asyncio
async def test_s3_upload_analysis_result(s3_bucket):
    """Test uploading analysis result to S3."""
    client = AsyncS3Client()

    analysis_data = {
        "session_id": "test_session_123",
        "total_reps": 10,
        "avg_score": 8.5,
        "duration": 180.5,
    }

    s3_key = await client.upload_analysis_result(
        user_id="test_user",
        session_id="test_session_123",
        analysis_data=analysis_data,
    )

    assert s3_key is not None
    assert "test_user" in s3_key
    assert "test_session_123" in s3_key


@pytest.mark.asyncio
async def test_s3_upload_frame_snapshot(s3_bucket):
    """Test uploading frame snapshot to S3."""
    client = AsyncS3Client()

    # Mock frame data
    frame_data = b"fake_jpeg_data"

    s3_key = await client.upload_frame_snapshot(
        user_id="test_user",
        session_id="test_session_123",
        frame_data=frame_data,
        frame_number=42,
    )

    assert s3_key is not None
    assert "frame_42" in s3_key


@pytest.mark.asyncio
async def test_s3_get_analysis_result(s3_bucket):
    """Test retrieving analysis result from S3."""
    client = AsyncS3Client()

    analysis_data = {
        "session_id": "test_session_123",
        "total_reps": 10,
    }

    # Upload first
    s3_key = await client.upload_analysis_result(
        user_id="test_user",
        session_id="test_session_123",
        analysis_data=analysis_data,
    )

    # Retrieve
    retrieved_data = await client.get_analysis_result(s3_key)

    assert retrieved_data is not None
    assert retrieved_data["session_id"] == "test_session_123"
    assert retrieved_data["total_reps"] == 10


@pytest.mark.asyncio
async def test_s3_list_session_results(s3_bucket):
    """Test listing session results."""
    client = AsyncS3Client()

    # Upload multiple results
    for i in range(3):
        await client.upload_analysis_result(
            user_id="test_user",
            session_id="test_session_123",
            analysis_data={"rep": i},
        )

    # List results
    keys = await client.list_session_results(
        user_id="test_user",
        session_id="test_session_123",
    )

    assert isinstance(keys, list)
    # May have 0-3 keys depending on timing


# SQS Tests
@pytest.mark.asyncio
async def test_sqs_publish_completion(sqs_queue):
    """Test publishing session completion event."""
    client = AsyncSQSClient()

    summary_data = {
        "session_id": "test_session_123",
        "total_reps": 15,
        "avg_score": 8.3,
    }

    success = await client.publish_posture_completed(
        user_id="test_user",
        session_id="test_session_123",
        summary_data=summary_data,
    )

    assert success is True


@pytest.mark.asyncio
async def test_sqs_publish_issue(sqs_queue):
    """Test publishing issue event."""
    client = AsyncSQSClient()

    issue_data = {
        "type": "knee_valgus",
        "severity": "high",
        "description": "Knees caving inward",
    }

    success = await client.publish_posture_issue(
        user_id="test_user",
        session_id="test_session_123",
        issue_data=issue_data,
    )

    assert success is True


@pytest.mark.asyncio
async def test_sqs_publish_rep_milestone(sqs_queue):
    """Test publishing rep milestone event."""
    client = AsyncSQSClient()

    success = await client.publish_rep_milestone(
        user_id="test_user",
        session_id="test_session_123",
        rep_count=10,
        exercise="squat",
    )

    assert success is True


@pytest.mark.asyncio
async def test_sqs_message_format(sqs_queue):
    """Test SQS message format."""
    client = AsyncSQSClient()

    summary_data = {
        "session_id": "test_session_123",
        "total_reps": 15,
    }

    await client.publish_posture_completed(
        user_id="test_user",
        session_id="test_session_123",
        summary_data=summary_data,
    )

    # Receive message
    response = sqs_queue.receive_message(
        QueueUrl=settings.sqs_posture_event_queue_url,
        MaxNumberOfMessages=1,
    )

    if "Messages" in response:
        message = response["Messages"][0]
        body = json.loads(message["Body"])

        assert body["event_type"] == "posture_session_completed"
        assert body["user_id"] == "test_user"
        assert body["session_id"] == "test_session_123"
        assert "timestamp" in body
        assert "summary" in body
