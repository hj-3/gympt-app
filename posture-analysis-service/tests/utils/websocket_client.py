"""WebSocket test client utilities."""
import asyncio
import json
import base64
from typing import Optional, Dict, Any, Callable
import websockets
from websockets.client import WebSocketClientProtocol
import logging

logger = logging.getLogger(__name__)


class WebSocketTestClient:
    """Helper class for WebSocket testing."""

    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self.messages: list = []
        self.is_connected = False

    async def connect(self, session_id: str):
        """Connect to WebSocket endpoint."""
        self.session_id = session_id
        uri = f"{self.base_url}/ws/posture/{session_id}"

        try:
            self.websocket = await websockets.connect(uri)
            self.is_connected = True
            logger.info(f"Connected to {uri}")

            # Wait for welcome message
            welcome = await self.receive_message(timeout=5.0)
            return welcome

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    async def disconnect(self):
        """Disconnect from WebSocket."""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from WebSocket")

    async def send_message(self, message: Dict[str, Any]):
        """Send JSON message to server."""
        if not self.websocket:
            raise RuntimeError("Not connected")

        await self.websocket.send(json.dumps(message))
        logger.debug(f"Sent message: {message.get('type')}")

    async def receive_message(self, timeout: float = 10.0) -> Dict[str, Any]:
        """Receive JSON message from server."""
        if not self.websocket:
            raise RuntimeError("Not connected")

        try:
            message_str = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout
            )
            message = json.loads(message_str)
            self.messages.append(message)
            logger.debug(f"Received message: {message.get('type')}")
            return message

        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for message ({timeout}s)")
            raise

    async def send_frame(
        self,
        frame_data: str,
        exercise: str = "squat"
    ):
        """Send a frame message."""
        await self.send_message({
            "type": "frame",
            "frame": frame_data,
            "exercise": exercise
        })

    async def send_exercise_change(self, exercise: str):
        """Send exercise change message."""
        await self.send_message({
            "type": "exercise",
            "exercise": exercise
        })

    async def send_ping(self):
        """Send ping message."""
        await self.send_message({"type": "ping"})

    async def wait_for_analysis(self, timeout: float = 10.0) -> Dict[str, Any]:
        """Wait for analysis message."""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            message = await self.receive_message(timeout=timeout)
            if message.get("type") == "analysis":
                return message

        raise TimeoutError("No analysis message received")

    async def wait_for_message_type(
        self,
        message_type: str,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Wait for specific message type."""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            message = await self.receive_message(timeout=timeout)
            if message.get("type") == message_type:
                return message

        raise TimeoutError(f"No '{message_type}' message received")

    async def receive_multiple_messages(
        self,
        count: int,
        timeout: float = 30.0
    ) -> list:
        """Receive multiple messages."""
        messages = []
        start_time = asyncio.get_event_loop().time()

        while len(messages) < count:
            remaining_time = timeout - (asyncio.get_event_loop().time() - start_time)
            if remaining_time <= 0:
                raise TimeoutError(f"Only received {len(messages)}/{count} messages")

            try:
                message = await self.receive_message(timeout=remaining_time)
                messages.append(message)
            except asyncio.TimeoutError:
                break

        return messages

    def get_messages_by_type(self, message_type: str) -> list:
        """Get all received messages of a specific type."""
        return [msg for msg in self.messages if msg.get("type") == message_type]

    def clear_messages(self):
        """Clear message history."""
        self.messages = []

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()


async def send_frame_sequence(
    client: WebSocketTestClient,
    frames: list,
    exercise: str = "squat",
    fps: int = 30,
    collect_responses: bool = True
) -> list:
    """
    Send a sequence of frames at specified FPS.

    Args:
        client: WebSocket client
        frames: List of base64-encoded frames
        exercise: Exercise type
        fps: Frames per second
        collect_responses: Whether to collect analysis responses

    Returns:
        List of analysis responses (if collect_responses=True)
    """
    responses = []
    frame_delay = 1.0 / fps

    for i, frame in enumerate(frames):
        await client.send_frame(frame, exercise)

        # Try to receive response (non-blocking)
        if collect_responses:
            try:
                response = await client.receive_message(timeout=0.5)
                responses.append(response)
            except asyncio.TimeoutError:
                pass

        # Maintain FPS
        if i < len(frames) - 1:
            await asyncio.sleep(frame_delay)

    return responses


async def simulate_concurrent_sessions(
    num_sessions: int,
    session_duration: float,
    base_url: str = "ws://localhost:8000"
) -> Dict[str, Any]:
    """
    Simulate multiple concurrent WebSocket sessions.

    Args:
        num_sessions: Number of concurrent sessions
        session_duration: Duration in seconds
        base_url: WebSocket base URL

    Returns:
        Statistics about the sessions
    """
    clients = []
    results = {
        "total_sessions": num_sessions,
        "successful_connections": 0,
        "failed_connections": 0,
        "total_messages_sent": 0,
        "total_messages_received": 0,
        "errors": []
    }

    # Create and connect clients
    for i in range(num_sessions):
        client = WebSocketTestClient(base_url)
        try:
            await client.connect(f"test-session-{i}")
            clients.append(client)
            results["successful_connections"] += 1
        except Exception as e:
            results["failed_connections"] += 1
            results["errors"].append(str(e))

    # Run sessions
    start_time = asyncio.get_event_loop().time()

    async def run_session(client: WebSocketTestClient):
        """Run a single session."""
        messages_sent = 0
        messages_received = 0

        try:
            while asyncio.get_event_loop().time() - start_time < session_duration:
                # Send ping
                await client.send_ping()
                messages_sent += 1

                # Receive pong
                try:
                    await client.wait_for_message_type("pong", timeout=2.0)
                    messages_received += 1
                except asyncio.TimeoutError:
                    pass

                await asyncio.sleep(1.0)

        except Exception as e:
            results["errors"].append(f"Session {client.session_id}: {str(e)}")

        return messages_sent, messages_received

    # Run all sessions concurrently
    session_results = await asyncio.gather(
        *[run_session(client) for client in clients],
        return_exceptions=True
    )

    # Aggregate results
    for sent, received in session_results:
        if isinstance(sent, Exception):
            continue
        results["total_messages_sent"] += sent
        results["total_messages_received"] += received

    # Disconnect all clients
    await asyncio.gather(
        *[client.disconnect() for client in clients],
        return_exceptions=True
    )

    return results
