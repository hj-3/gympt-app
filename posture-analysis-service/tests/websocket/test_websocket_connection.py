"""Test WebSocket connection management."""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.streaming.websocket_handler import WebSocketHandler


pytestmark = [pytest.mark.asyncio, pytest.mark.websocket]


class TestWebSocketConnection:
    """Test WebSocket connection lifecycle."""

    @pytest.fixture
    def ws_handler(self):
        """Create WebSocket handler."""
        return WebSocketHandler()

    async def test_connection_establishment(self, test_client):
        """Test successful WebSocket connection."""
        with test_client.websocket_connect("/ws/posture/test-session-001") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()

            assert data["type"] == "connected"
            assert data["session_id"] == "test-session-001"
            assert "message" in data

    async def test_connection_with_valid_session_id(self, test_client):
        """Test connection with valid session ID."""
        session_ids = ["user-123", "session-abc-xyz", "test_session_001"]

        for session_id in session_ids:
            with test_client.websocket_connect(f"/ws/posture/{session_id}") as websocket:
                data = websocket.receive_json()
                assert data["type"] == "connected"
                assert data["session_id"] == session_id

    async def test_connection_counter_increment(self, ws_handler):
        """Test active connections counter increments."""
        initial_count = ws_handler.active_connections

        # Mock websocket
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()

        await ws_handler.connect(mock_ws, "test-session-001")

        assert ws_handler.active_connections == initial_count + 1

    async def test_disconnect_reduces_counter(self, ws_handler):
        """Test disconnect reduces active connections counter."""
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()

        await ws_handler.connect(mock_ws, "test-session-001")
        initial_count = ws_handler.active_connections

        await ws_handler.disconnect("test-session-001")

        assert ws_handler.active_connections == initial_count - 1

    async def test_max_connections_limit(self):
        """Test max connections limit enforcement."""
        from app.config import settings

        # Create handler with settings
        ws_handler = WebSocketHandler()

        # Fill up to max connections
        mock_websockets = []
        for i in range(settings.max_websocket_connections):
            mock_ws = AsyncMock()
            mock_ws.accept = AsyncMock()
            await ws_handler.connect(mock_ws, f"session-{i}")
            mock_websockets.append(mock_ws)

        # Try to connect one more (should be rejected)
        rejected_ws = AsyncMock()
        rejected_ws.accept = AsyncMock()
        rejected_ws.close = AsyncMock()

        await ws_handler.connect(rejected_ws, "session-overflow")

        # Should have called close with max connections reason
        rejected_ws.close.assert_called_once()
        call_args = rejected_ws.close.call_args
        assert call_args.kwargs.get("code") == 1008
        assert "Max connections" in call_args.kwargs.get("reason", "")

        # Cleanup
        for i, ws in enumerate(mock_websockets):
            await ws_handler.disconnect(f"session-{i}")

    async def test_concurrent_connections(self, test_client):
        """Test multiple concurrent connections."""
        num_connections = 10
        websockets = []

        try:
            # Open multiple connections
            for i in range(num_connections):
                ws = test_client.websocket_connect(f"/ws/posture/concurrent-{i}")
                ws.__enter__()
                websockets.append(ws)

                # Verify welcome message
                data = ws.receive_json()
                assert data["type"] == "connected"

            # All should be connected
            assert len(websockets) == num_connections

        finally:
            # Cleanup
            for ws in websockets:
                ws.__exit__(None, None, None)

    async def test_heartbeat_ping_pong(self, test_client):
        """Test ping/pong heartbeat mechanism."""
        with test_client.websocket_connect("/ws/posture/heartbeat-test") as websocket:
            # Receive welcome
            websocket.receive_json()

            # Send ping
            websocket.send_json({"type": "ping"})

            # Should receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"

    async def test_multiple_pings(self, test_client):
        """Test multiple ping/pong exchanges."""
        with test_client.websocket_connect("/ws/posture/multi-ping-test") as websocket:
            # Receive welcome
            websocket.receive_json()

            # Send multiple pings
            for i in range(5):
                websocket.send_json({"type": "ping"})
                response = websocket.receive_json()
                assert response["type"] == "pong"

    async def test_disconnect_cleanup(self, ws_handler):
        """Test proper cleanup on disconnect."""
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()

        session_id = "cleanup-test-session"
        await ws_handler.connect(mock_ws, session_id)

        # Verify session is tracked
        assert session_id in ws_handler.connections
        assert session_id in ws_handler.frame_count

        # Disconnect
        await ws_handler.disconnect(session_id)

        # Verify cleanup
        assert session_id not in ws_handler.connections
        assert session_id not in ws_handler.frame_count

    async def test_reconnection(self, test_client):
        """Test reconnection with same session ID."""
        session_id = "reconnect-test"

        # First connection
        with test_client.websocket_connect(f"/ws/posture/{session_id}") as ws1:
            data = ws1.receive_json()
            assert data["session_id"] == session_id

        # Second connection (reconnect)
        with test_client.websocket_connect(f"/ws/posture/{session_id}") as ws2:
            data = ws2.receive_json()
            assert data["session_id"] == session_id

    async def test_multiple_sessions_per_user(self, test_client):
        """Test multiple sessions for same user (different session IDs)."""
        user_id = "user-123"
        session_ids = [f"{user_id}-session-{i}" for i in range(3)]

        websockets = []

        try:
            # Open multiple sessions
            for session_id in session_ids:
                ws = test_client.websocket_connect(f"/ws/posture/{session_id}")
                ws.__enter__()
                websockets.append(ws)

                data = ws.receive_json()
                assert data["session_id"] == session_id

            # All should be connected independently
            assert len(websockets) == 3

        finally:
            for ws in websockets:
                ws.__exit__(None, None, None)

    async def test_connection_with_health_check(self, test_client):
        """Test connection while health check endpoint works."""
        # Check health endpoint
        response = test_client.get("/health")
        assert response.status_code == 200

        # Connect WebSocket
        with test_client.websocket_connect("/ws/posture/health-test") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

        # Health check should still work
        response = test_client.get("/health")
        assert response.status_code == 200

    async def test_connection_tracking_in_health(self, test_client):
        """Test active connections reported in health check."""
        # Check initial count
        response = test_client.get("/health")
        initial_count = response.json()["active_sessions"]

        # Connect
        with test_client.websocket_connect("/ws/posture/tracking-test") as websocket:
            websocket.receive_json()

            # Check count increased
            response = test_client.get("/health")
            current_count = response.json()["active_sessions"]
            assert current_count == initial_count + 1

        # After disconnect, count should decrease
        response = test_client.get("/health")
        final_count = response.json()["active_sessions"]
        assert final_count == initial_count

    async def test_graceful_disconnect(self, ws_handler):
        """Test graceful disconnect doesn't raise errors."""
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()

        session_id = "graceful-disconnect"
        await ws_handler.connect(mock_ws, session_id)

        # Disconnect should not raise
        await ws_handler.disconnect(session_id)

        # Double disconnect should also not raise
        await ws_handler.disconnect(session_id)

    async def test_disconnect_nonexistent_session(self, ws_handler):
        """Test disconnecting non-existent session doesn't error."""
        # Should not raise
        await ws_handler.disconnect("nonexistent-session")

    @pytest.mark.slow
    async def test_connection_stability(self, test_client):
        """Test connection stability over time."""
        with test_client.websocket_connect("/ws/posture/stability-test") as websocket:
            websocket.receive_json()  # Welcome

            # Send pings periodically
            for i in range(10):
                websocket.send_json({"type": "ping"})
                response = websocket.receive_json()
                assert response["type"] == "pong"

                await asyncio.sleep(0.5)


@pytest.mark.performance
class TestWebSocketPerformance:
    """Test WebSocket connection performance."""

    async def test_connection_time(self, test_client):
        """Test connection establishment time."""
        import time

        start = time.time()

        with test_client.websocket_connect("/ws/posture/perf-test"):
            pass

        elapsed = time.time() - start

        # Connection should be fast (<1s)
        assert elapsed < 1.0

    async def test_rapid_connect_disconnect(self, test_client):
        """Test rapid connection and disconnection cycles."""
        for i in range(20):
            with test_client.websocket_connect(f"/ws/posture/rapid-{i}") as websocket:
                data = websocket.receive_json()
                assert data["type"] == "connected"
