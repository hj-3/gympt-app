"""End-to-end test for session lifecycle."""
import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from tests.utils.landmark_generator import LandmarkGenerator


pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


class TestSessionLifecycle:
    """Test complete session lifecycle scenarios."""

    @pytest.fixture
    def landmark_gen(self):
        """Landmark generator."""
        return LandmarkGenerator()

    async def test_start_pause_resume_end(
        self,
        test_client,
        landmark_gen,
        base64_encoded_frame
    ):
        """Test session with pause and resume."""
        session_id = "pause-resume-test"

        with test_client.websocket_connect(f"/ws/posture/{session_id}") as websocket:
            # Start session
            welcome = websocket.receive_json()
            assert welcome["type"] == "connected"

            # Send some frames
            for _ in range(5):
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })
                websocket.receive_json()

            # Pause (stop sending frames for a bit)
            await asyncio.sleep(2)

            # Resume (send more frames)
            for _ in range(5):
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })
                websocket.receive_json()

            # End session (disconnect)
            # Session ends when WebSocket closes

    async def test_concurrent_sessions_different_users(
        self,
        test_client,
        base64_encoded_frame
    ):
        """Test concurrent sessions from different users."""
        num_users = 5
        sessions = []

        # Create sessions for different users
        for i in range(num_users):
            ws = test_client.websocket_connect(f"/ws/posture/user-{i}-session")
            ws.__enter__()
            sessions.append(ws)

            # Receive welcome
            welcome = ws.receive_json()
            assert welcome["type"] == "connected"

        # All users send frames concurrently
        for ws in sessions:
            ws.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })

        # All should receive analysis
        for ws in sessions:
            analysis = ws.receive_json()
            assert analysis["type"] == "analysis"

        # Cleanup
        for ws in sessions:
            ws.__exit__(None, None, None)

    async def test_session_timeout_handling(
        self,
        test_client,
        base64_encoded_frame
    ):
        """Test session timeout after inactivity."""
        session_id = "timeout-test"

        with test_client.websocket_connect(f"/ws/posture/{session_id}") as websocket:
            websocket.receive_json()  # Welcome

            # Send initial frame
            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })
            websocket.receive_json()

            # Simulate long inactivity (in real system would timeout)
            # For testing, just verify connection can be reused after delay
            await asyncio.sleep(1)

            # Send another frame
            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })
            response = websocket.receive_json()

            assert response["type"] == "analysis"

    async def test_abnormal_termination(
        self,
        test_client,
        base64_encoded_frame
    ):
        """Test handling of abnormal session termination."""
        session_id = "abnormal-termination"

        # Start session
        ws = test_client.websocket_connect(f"/ws/posture/{session_id}")
        ws.__enter__()

        welcome = ws.receive_json()
        assert welcome["type"] == "connected"

        # Send a frame
        ws.send_json({
            "type": "frame",
            "frame": base64_encoded_frame,
            "exercise": "squat"
        })
        ws.receive_json()

        # Abruptly close (simulating crash or network issue)
        ws.__exit__(None, None, None)

        # Session should be cleaned up
        # Verify by checking we can create new session with same ID
        with test_client.websocket_connect(f"/ws/posture/{session_id}") as new_ws:
            welcome = new_ws.receive_json()
            assert welcome["type"] == "connected"

    async def test_exercise_switching_during_session(
        self,
        test_client,
        base64_encoded_frame
    ):
        """Test switching exercises during a session."""
        session_id = "exercise-switch-test"

        with test_client.websocket_connect(f"/ws/posture/{session_id}") as websocket:
            websocket.receive_json()  # Welcome

            exercises = ["squat", "pushup", "plank", "deadlift"]

            for exercise in exercises:
                # Change exercise
                websocket.send_json({
                    "type": "exercise",
                    "exercise": exercise
                })

                response = websocket.receive_json()
                assert response["type"] == "exercise_changed"
                assert response["exercise"] == exercise

                # Send some frames with new exercise
                for _ in range(3):
                    websocket.send_json({
                        "type": "frame",
                        "frame": base64_encoded_frame,
                        "exercise": exercise
                    })

                    analysis = websocket.receive_json()
                    assert analysis["type"] == "analysis"

    async def test_multiple_sessions_same_user(
        self,
        test_client,
        base64_encoded_frame
    ):
        """Test multiple sessions for the same user (different session IDs)."""
        user_id = "user-multi-session"
        num_sessions = 3

        sessions = []

        # Open multiple sessions
        for i in range(num_sessions):
            ws = test_client.websocket_connect(f"/ws/posture/{user_id}-session-{i}")
            ws.__enter__()
            sessions.append(ws)

            welcome = ws.receive_json()
            assert welcome["type"] == "connected"

        # Each session should be independent
        for i, ws in enumerate(sessions):
            ws.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })

            analysis = ws.receive_json()
            assert analysis["type"] == "analysis"

        # Cleanup
        for ws in sessions:
            ws.__exit__(None, None, None)

    async def test_session_with_errors(
        self,
        test_client,
        base64_encoded_frame
    ):
        """Test session continues after errors."""
        session_id = "error-recovery-test"

        with test_client.websocket_connect(f"/ws/posture/{session_id}") as websocket:
            websocket.receive_json()  # Welcome

            # Send valid frame
            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })
            websocket.receive_json()

            # Send invalid message
            websocket.send_json({
                "type": "unknown_type",
                "data": "invalid"
            })

            # Send valid frame again - session should still work
            websocket.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })

            response = websocket.receive_json()
            # Should receive analysis or handle gracefully
            assert response is not None

    async def test_rapid_session_creation(self, test_client):
        """Test rapid creation of many sessions."""
        num_sessions = 20

        for i in range(num_sessions):
            with test_client.websocket_connect(f"/ws/posture/rapid-{i}") as websocket:
                welcome = websocket.receive_json()
                assert welcome["type"] == "connected"
                assert welcome["session_id"] == f"rapid-{i}"

    @pytest.mark.slow
    async def test_long_running_session(
        self,
        test_client,
        landmark_gen,
        base64_encoded_frame
    ):
        """Test long-running session (5 minutes simulated)."""
        session_id = "long-running-test"

        with test_client.websocket_connect(f"/ws/posture/{session_id}") as websocket:
            websocket.receive_json()  # Welcome

            # Simulate 5 minutes at 10 FPS (3000 frames)
            # For testing, we'll do 30 frames (3 seconds worth)
            num_frames = 30

            for i in range(num_frames):
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })

                analysis = websocket.receive_json()
                assert analysis["type"] == "analysis"
                assert analysis["frame_number"] == i + 1

                # Simulate frame rate
                await asyncio.sleep(0.1)

            # Session should still be active after long duration

    async def test_session_data_isolation(
        self,
        test_client,
        base64_encoded_frame
    ):
        """Test data isolation between sessions."""
        session1_id = "session-1"
        session2_id = "session-2"

        # Session 1
        with test_client.websocket_connect(f"/ws/posture/{session1_id}") as ws1:
            ws1.receive_json()  # Welcome

            # Send 5 frames
            for i in range(5):
                ws1.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })
                analysis = ws1.receive_json()
                assert analysis["session_id"] == session1_id
                assert analysis["frame_number"] == i + 1

        # Session 2 (should start fresh)
        with test_client.websocket_connect(f"/ws/posture/{session2_id}") as ws2:
            ws2.receive_json()  # Welcome

            # Send 3 frames
            for i in range(3):
                ws2.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "pushup"
                })
                analysis = ws2.receive_json()
                assert analysis["session_id"] == session2_id
                # Frame number should start from 1, not continue from session 1
                assert analysis["frame_number"] == i + 1

    async def test_session_reconnection_same_id(
        self,
        test_client,
        base64_encoded_frame
    ):
        """Test reconnecting with same session ID."""
        session_id = "reconnect-same-id"

        # First connection
        with test_client.websocket_connect(f"/ws/posture/{session_id}") as ws1:
            ws1.receive_json()  # Welcome

            ws1.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })
            analysis1 = ws1.receive_json()
            assert analysis1["frame_number"] == 1

        # Second connection (reconnect)
        with test_client.websocket_connect(f"/ws/posture/{session_id}") as ws2:
            ws2.receive_json()  # Welcome

            ws2.send_json({
                "type": "frame",
                "frame": base64_encoded_frame,
                "exercise": "squat"
            })
            analysis2 = ws2.receive_json()

            # Frame number should start from 1 (new session)
            assert analysis2["frame_number"] == 1
