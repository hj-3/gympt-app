import pytest
import pytest_asyncio
import sys
import os
import asyncio
import base64
from pathlib import Path
from typing import Dict, List, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np
import cv2
from fastapi.testclient import TestClient
from moto import mock_aws
import boto3

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.clients.redis_client import redis_client
from app.config import settings


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session scope."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """FastAPI test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def websocket_test_client():
    """WebSocket test client fixture."""
    from websockets.client import connect

    async def _create_websocket(session_id: str):
        uri = f"ws://localhost:8000/ws/posture/{session_id}"
        return await connect(uri)

    return _create_websocket


@pytest.fixture
def mock_pose_data():
    """Mock pose estimation data for generic use."""
    return {
        "landmarks": [],
        "confidence": 0.85,
        "keypoints": {
            "left_shoulder": {"x": 0.4, "y": 0.35, "confidence": 0.9},
            "right_shoulder": {"x": 0.6, "y": 0.35, "confidence": 0.9},
            "left_hip": {"x": 0.42, "y": 0.6, "confidence": 0.9},
            "right_hip": {"x": 0.58, "y": 0.6, "confidence": 0.9},
            "left_knee": {"x": 0.4, "y": 0.75, "confidence": 0.9},
            "right_knee": {"x": 0.6, "y": 0.75, "confidence": 0.9},
            "left_ankle": {"x": 0.38, "y": 0.9, "confidence": 0.9},
            "right_ankle": {"x": 0.62, "y": 0.9, "confidence": 0.9},
            "left_wrist": {"x": 0.35, "y": 0.5, "confidence": 0.9},
            "right_wrist": {"x": 0.65, "y": 0.5, "confidence": 0.9},
            "left_elbow": {"x": 0.37, "y": 0.42, "confidence": 0.9},
            "right_elbow": {"x": 0.63, "y": 0.42, "confidence": 0.9},
        }
    }


@pytest.fixture
def mock_squat_down_pose():
    """Mock pose data for squat in down position."""
    return {
        "landmarks": [],
        "confidence": 0.90,
        "keypoints": {
            "left_shoulder": {"x": 0.4, "y": 0.30, "confidence": 0.95},
            "right_shoulder": {"x": 0.6, "y": 0.30, "confidence": 0.95},
            "left_hip": {"x": 0.42, "y": 0.65, "confidence": 0.95},
            "right_hip": {"x": 0.58, "y": 0.65, "confidence": 0.95},
            "left_knee": {"x": 0.4, "y": 0.70, "confidence": 0.95},
            "right_knee": {"x": 0.6, "y": 0.70, "confidence": 0.95},
            "left_ankle": {"x": 0.38, "y": 0.90, "confidence": 0.95},
            "right_ankle": {"x": 0.62, "y": 0.90, "confidence": 0.95}
        }
    }


@pytest.fixture
def mock_squat_up_pose():
    """Mock pose data for squat in up position."""
    return {
        "landmarks": [],
        "confidence": 0.92,
        "keypoints": {
            "left_shoulder": {"x": 0.4, "y": 0.25, "confidence": 0.95},
            "right_shoulder": {"x": 0.6, "y": 0.25, "confidence": 0.95},
            "left_hip": {"x": 0.42, "y": 0.50, "confidence": 0.95},
            "right_hip": {"x": 0.58, "y": 0.50, "confidence": 0.95},
            "left_knee": {"x": 0.4, "y": 0.75, "confidence": 0.95},
            "right_knee": {"x": 0.6, "y": 0.75, "confidence": 0.95},
            "left_ankle": {"x": 0.38, "y": 0.90, "confidence": 0.95},
            "right_ankle": {"x": 0.62, "y": 0.90, "confidence": 0.95}
        }
    }


@pytest.fixture
def mock_pushup_down_pose():
    """Mock pose data for pushup in down position."""
    return {
        "landmarks": [],
        "confidence": 0.88,
        "keypoints": {
            "left_shoulder": {"x": 0.35, "y": 0.48, "confidence": 0.90},
            "right_shoulder": {"x": 0.65, "y": 0.48, "confidence": 0.90},
            "left_elbow": {"x": 0.30, "y": 0.50, "confidence": 0.90},
            "right_elbow": {"x": 0.70, "y": 0.50, "confidence": 0.90},
            "left_wrist": {"x": 0.28, "y": 0.52, "confidence": 0.90},
            "right_wrist": {"x": 0.72, "y": 0.52, "confidence": 0.90},
            "left_hip": {"x": 0.40, "y": 0.50, "confidence": 0.90},
            "right_hip": {"x": 0.60, "y": 0.50, "confidence": 0.90},
        }
    }


@pytest.fixture
def mock_pushup_up_pose():
    """Mock pose data for pushup in up position."""
    return {
        "landmarks": [],
        "confidence": 0.89,
        "keypoints": {
            "left_shoulder": {"x": 0.35, "y": 0.38, "confidence": 0.92},
            "right_shoulder": {"x": 0.65, "y": 0.38, "confidence": 0.92},
            "left_elbow": {"x": 0.30, "y": 0.42, "confidence": 0.92},
            "right_elbow": {"x": 0.70, "y": 0.42, "confidence": 0.92},
            "left_wrist": {"x": 0.28, "y": 0.52, "confidence": 0.92},
            "right_wrist": {"x": 0.72, "y": 0.52, "confidence": 0.92},
            "left_hip": {"x": 0.40, "y": 0.40, "confidence": 0.92},
            "right_hip": {"x": 0.60, "y": 0.40, "confidence": 0.92},
        }
    }


@pytest.fixture
def sample_frame_480p():
    """Generate a sample 480p frame (numpy array)."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_720p():
    """Generate a sample 720p frame (numpy array)."""
    return np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_1080p():
    """Generate a sample 1080p frame (numpy array)."""
    return np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)


@pytest.fixture
def base64_encoded_frame(sample_frame_480p):
    """Generate a base64 encoded frame for WebSocket testing."""
    _, buffer = cv2.imencode('.jpg', sample_frame_480p)
    frame_bytes = buffer.tobytes()
    return base64.b64encode(frame_bytes).decode('utf-8')


@pytest.fixture
def mock_mediapipe_landmarks():
    """Mock MediaPipe 33-point landmarks."""
    landmarks = []
    # MediaPipe has 33 landmarks
    for i in range(33):
        landmarks.append({
            "x": 0.5 + (i % 3 - 1) * 0.1,
            "y": 0.3 + (i // 3) * 0.02,
            "z": 0.0,
            "visibility": 0.9
        })
    return landmarks


@pytest_asyncio.fixture
async def mock_redis():
    """Mock Redis client."""
    with patch('app.clients.redis_client.redis_client') as mock:
        mock.ping = AsyncMock(return_value=True)
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=True)
        mock.publish = AsyncMock(return_value=1)
        mock.close = AsyncMock()
        yield mock


@pytest.fixture
def mock_aws_credentials():
    """Mocked AWS credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-2'


@pytest.fixture
def mock_dynamodb(mock_aws_credentials):
    """Mock DynamoDB using moto."""
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')

        # Create posture events table
        table = dynamodb.create_table(
            TableName='gympt-posture-events-local',
            KeySchema=[
                {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'session_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        yield dynamodb


@pytest.fixture
def mock_s3(mock_aws_credentials):
    """Mock S3 using moto."""
    with mock_aws():
        s3 = boto3.client('s3', region_name='ap-northeast-2')

        # Create bucket
        s3.create_bucket(
            Bucket='gympt-media-local',
            CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-2'}
        )

        yield s3


@pytest.fixture
def mock_sqs(mock_aws_credentials):
    """Mock SQS using moto."""
    with mock_aws():
        sqs = boto3.client('sqs', region_name='ap-northeast-2')

        # Create queue
        response = sqs.create_queue(
            QueueName='gympt-posture-events-local'
        )

        queue_url = response['QueueUrl']

        yield sqs, queue_url


@pytest.fixture
def squat_rep_sequence():
    """Generate a sequence of poses representing 10 squat reps."""
    sequence = []

    for rep in range(10):
        # Starting position
        sequence.append({
            "landmarks": [],
            "confidence": 0.90,
            "keypoints": {
                "left_hip": {"x": 0.42, "y": 0.50, "confidence": 0.95},
                "left_knee": {"x": 0.40, "y": 0.75, "confidence": 0.95},
                "left_ankle": {"x": 0.38, "y": 0.90, "confidence": 0.95}
            }
        })

        # Down position
        sequence.append({
            "landmarks": [],
            "confidence": 0.88,
            "keypoints": {
                "left_hip": {"x": 0.42, "y": 0.68, "confidence": 0.93},
                "left_knee": {"x": 0.40, "y": 0.72, "confidence": 0.93},
                "left_ankle": {"x": 0.38, "y": 0.90, "confidence": 0.93}
            }
        })

        # Up position
        sequence.append({
            "landmarks": [],
            "confidence": 0.91,
            "keypoints": {
                "left_hip": {"x": 0.42, "y": 0.52, "confidence": 0.94},
                "left_knee": {"x": 0.40, "y": 0.74, "confidence": 0.94},
                "left_ankle": {"x": 0.38, "y": 0.90, "confidence": 0.94}
            }
        })

    return sequence


@pytest.fixture
def pushup_rep_sequence():
    """Generate a sequence of poses representing 20 pushup reps."""
    sequence = []

    for rep in range(20):
        # Up position
        sequence.append({
            "landmarks": [],
            "confidence": 0.89,
            "keypoints": {
                "left_shoulder": {"x": 0.35, "y": 0.38, "confidence": 0.92},
                "left_wrist": {"x": 0.28, "y": 0.52, "confidence": 0.92},
            }
        })

        # Down position
        sequence.append({
            "landmarks": [],
            "confidence": 0.87,
            "keypoints": {
                "left_shoulder": {"x": 0.35, "y": 0.48, "confidence": 0.90},
                "left_wrist": {"x": 0.28, "y": 0.52, "confidence": 0.90},
            }
        })

        # Up position again
        sequence.append({
            "landmarks": [],
            "confidence": 0.89,
            "keypoints": {
                "left_shoulder": {"x": 0.35, "y": 0.39, "confidence": 0.91},
                "left_wrist": {"x": 0.28, "y": 0.52, "confidence": 0.91},
            }
        })

    return sequence


@pytest.fixture
def test_session_data():
    """Sample session data for testing."""
    return {
        "session_id": "test-session-001",
        "user_id": "user-123",
        "exercise_type": "squat",
        "start_time": "2026-05-19T10:00:00Z",
        "end_time": "2026-05-19T10:05:00Z",
        "total_reps": 10,
        "average_score": 8.5,
        "duration_seconds": 300,
        "form_issues": ["knee_valgus", "depth"],
        "status": "completed"
    }
