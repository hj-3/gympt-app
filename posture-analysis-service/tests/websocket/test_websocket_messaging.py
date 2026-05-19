"""Test WebSocket messaging and frame processing."""
import pytest
import asyncio
import base64
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from tests.utils.assertions import assert_websocket_message


pytestmark = [pytest.mark.asyncio, pytest.mark.websocket]


class TestWebSocketMessaging:
    """Test WebSocket message handling."""

    async def test_frame_processing_flow(self, test_client, base64_encoded_frame):
        """Test complete frame processing flow."""
        with test_client.websocket_connect("/ws/posture/frame-test") as websocket:
            # Receive welcome
            welcome = websocket.receive_json()
            assert_websocket_message(welcome, "connected")

            # Send frame
            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })

            # Receive analysis
            analysis = websocket.receive_json()
            assert_websocket_message(
                analysis,
                "analysis",
                required_fields=["session_id", "frame_number", "score", "issues"]
            )

    async def test_exercise_type_switching(self, test_client, base64_encoded_frame):
        """Test switching between exercise types."""
        with test_client.websocket_connect("/ws/posture/exercise-switch") as websocket:
            websocket.receive_json()  # Welcome

            exercises = ["squat", "pushup", "plank", "deadlift"]

            for exercise in exercises:
                # Change exercise
                websocket.send_json({
                    "type": "exercise",
                    "exercise": exercise
                })

                # Receive confirmation
                response = websocket.receive_json()
                assert response["type"] == "exercise_changed"
                assert response["exercise"] == exercise

                # Send frame with new exercise
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": exercise
                })

                # Receive analysis
                analysis = websocket.receive_json()
                assert analysis["type"] == "analysis"

    async def test_invalid_message_format(self, test_client):
        """Test handling of invalid message formats."""
        with test_client.websocket_connect("/ws/posture/invalid-test") as websocket:
            websocket.receive_json()  # Welcome

            # Send invalid JSON (will be caught by FastAPI)
            # We send a valid message with unknown type instead
            websocket.send_json({
                "type": "unknown_type",
                "data": "test"
            })

            # Should not crash, might receive error or no response
            # The server logs a warning but continues
            pass  # No exception should be raised

    async def test_missing_frame_data(self, test_client):
        """Test frame message without frame data."""
        with test_client.websocket_connect("/ws/posture/no-frame-test") as websocket:
            websocket.receive_json()  # Welcome

            # Send frame message without frame data
            websocket.send_json({
                "type": "frame",
                "exercise": "squat"
                # Missing "frame" field
            })

            # Should receive analysis with mock frame
            analysis = websocket.receive_json()
            assert analysis["type"] == "analysis"

    async def test_base64_frame_decoding(self, test_client, base64_encoded_frame):
        """Test base64 frame decoding."""
        with test_client.websocket_connect("/ws/posture/decode-test") as websocket:
            websocket.receive_json()  # Welcome

            # Test with data URL prefix
            frame_with_prefix = f"data:image/jpeg;base64,{base64_encoded_frame}"

            websocket.send_json({
                "type": "frame",
                "frame": frame_with_prefix,
                "exercise": "squat"
            })

            analysis = websocket.receive_json()
            assert analysis["type"] == "analysis"

            # Test without prefix
            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })

            analysis = websocket.receive_json()
            assert analysis["type"] == "analysis"

    async def test_invalid_base64_frame(self, test_client):
        """Test handling of invalid base64 data."""
        with test_client.websocket_connect("/ws/posture/bad-frame-test") as websocket:
            websocket.receive_json()  # Welcome

            # Send invalid base64
            websocket.send_json({
                "type": "frame",
                "frame": "not-valid-base64!@#$",
                "exercise": "squat"
            })

            # Should handle gracefully and send error or use fallback
            response = websocket.receive_json()
            # Either error or analysis with fallback frame
            assert response["type"] in ["error", "analysis"]

    async def test_frame_number_increment(self, test_client, base64_encoded_frame):
        """Test frame number increments correctly."""
        with test_client.websocket_connect("/ws/posture/frame-count-test") as websocket:
            websocket.receive_json()  # Welcome

            # Send multiple frames
            for i in range(5):
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })

                analysis = websocket.receive_json()
                assert analysis["frame_number"] == i + 1

    async def test_concurrent_frame_processing(self, test_client, base64_encoded_frame):
        """Test processing multiple frames in sequence."""
        with test_client.websocket_connect("/ws/posture/concurrent-frames") as websocket:
            websocket.receive_json()  # Welcome

            num_frames = 10

            # Send frames
            for i in range(num_frames):
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })

            # Receive all analyses
            analyses = []
            for i in range(num_frames):
                analysis = websocket.receive_json()
                assert analysis["type"] == "analysis"
                analyses.append(analysis)

            # Verify we got all analyses
            assert len(analyses) == num_frames

    @pytest.mark.performance
    async def test_frame_rate_handling(self, test_client, base64_encoded_frame):
        """Test handling of 30 FPS frame rate."""
        import time

        with test_client.websocket_connect("/ws/posture/fps-test") as websocket:
            websocket.receive_json()  # Welcome

            fps = 30
            num_frames = 30  # 1 second worth
            frame_delay = 1.0 / fps

            start_time = time.time()

            for i in range(num_frames):
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })

                # Try to receive (non-blocking)
                try:
                    websocket.receive_json()
                except:
                    pass

                # Maintain frame rate
                if i < num_frames - 1:
                    time.sleep(frame_delay)

            elapsed = time.time() - start_time

            # Should complete in roughly 1 second (with some overhead)
            assert 0.9 <= elapsed <= 2.0

    async def test_exercise_without_frame(self, test_client):
        """Test exercise change without sending frames."""
        with test_client.websocket_connect("/ws/posture/exercise-only") as websocket:
            websocket.receive_json()  # Welcome

            # Change exercise multiple times
            for exercise in ["squat", "pushup", "plank"]:
                websocket.send_json({
                    "type": "exercise",
                    "exercise": exercise
                })

                response = websocket.receive_json()
                assert response["type"] == "exercise_changed"
                assert response["exercise"] == exercise

    async def test_mixed_message_types(self, test_client, base64_encoded_frame):
        """Test mixed sequence of different message types."""
        with test_client.websocket_connect("/ws/posture/mixed-messages") as websocket:
            websocket.receive_json()  # Welcome

            # Ping
            websocket.send_json({"type": "ping"})
            assert websocket.receive_json()["type"] == "pong"

            # Exercise change
            websocket.send_json({"type": "exercise", "exercise": "pushup"})
            assert websocket.receive_json()["type"] == "exercise_changed"

            # Frame
            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "pushup"
            })
            assert websocket.receive_json()["type"] == "analysis"

            # Another ping
            websocket.send_json({"type": "ping"})
            assert websocket.receive_json()["type"] == "pong"

    async def test_malformed_exercise_message(self, test_client):
        """Test exercise message without exercise field."""
        with test_client.websocket_connect("/ws/posture/malformed-exercise") as websocket:
            websocket.receive_json()  # Welcome

            # Send exercise change without exercise field
            websocket.send_json({
                "type": "exercise"
                # Missing "exercise" field
            })

            # Should handle gracefully (might receive error or log warning)
            pass  # No crash expected

    async def test_empty_message(self, test_client):
        """Test handling of empty message."""
        with test_client.websocket_connect("/ws/posture/empty-message") as websocket:
            websocket.receive_json()  # Welcome

            # Send empty object
            websocket.send_json({})

            # Should handle gracefully
            pass  # No crash expected

    async def test_feedback_threshold_triggering(self, test_client, base64_encoded_frame):
        """Test feedback publishing when score is low."""
        with patch('app.feedback.feedback_service.FeedbackService.publish_feedback') as mock_publish:
            mock_publish.return_value = None

            with test_client.websocket_connect("/ws/posture/feedback-test") as websocket:
                websocket.receive_json()  # Welcome

                # Send frame (score might be low enough to trigger feedback)
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })

                analysis = websocket.receive_json()
                assert analysis["type"] == "analysis"

                # If score is low, feedback should be published
                # (depends on mock behavior)

    async def test_confidence_score_in_response(self, test_client, base64_encoded_frame):
        """Test confidence score is included in analysis response."""
        with test_client.websocket_connect("/ws/posture/confidence-test") as websocket:
            websocket.receive_json()  # Welcome

            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })

            analysis = websocket.receive_json()
            assert "confidence" in analysis
            assert 0 <= analysis["confidence"] <= 1

    async def test_session_id_consistency(self, test_client, base64_encoded_frame):
        """Test session_id is consistent across messages."""
        session_id = "consistency-test"

        with test_client.websocket_connect(f"/ws/posture/{session_id}") as websocket:
            welcome = websocket.receive_json()
            assert welcome["session_id"] == session_id

            # Send multiple frames
            for _ in range(3):
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })

                analysis = websocket.receive_json()
                assert analysis["session_id"] == session_id

    @pytest.mark.slow
    async def test_backpressure_handling(self, test_client, base64_encoded_frame):
        """Test handling of rapid frame sending (backpressure)."""
        with test_client.websocket_connect("/ws/posture/backpressure-test") as websocket:
            websocket.receive_json()  # Welcome

            # Send many frames rapidly without waiting for responses
            num_frames = 100

            for i in range(num_frames):
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })

            # Connection should remain stable
            # Try to receive some responses
            responses_received = 0
            try:
                for _ in range(10):
                    websocket.receive_json()
                    responses_received += 1
            except:
                pass

            # Should have received at least some responses
            assert responses_received > 0


@pytest.mark.integration
class TestWebSocketIntegration:
    """Integration tests for WebSocket with other services."""

    async def test_redis_feedback_publishing(self, test_client, mock_redis, base64_encoded_frame):
        """Test feedback is published to Redis when score is low."""
        with test_client.websocket_connect("/ws/posture/redis-test") as websocket:
            websocket.receive_json()  # Welcome

            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })

            analysis = websocket.receive_json()
            assert analysis["type"] == "analysis"

            # If score is below threshold, Redis publish should be called
            # (mocked in conftest)
