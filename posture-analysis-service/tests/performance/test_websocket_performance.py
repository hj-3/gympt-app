"""WebSocket performance tests."""
import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from tests.utils.assertions import assert_performance_metrics


pytestmark = [pytest.mark.asyncio, pytest.mark.performance]


class TestWebSocketPerformance:
    """Test WebSocket performance characteristics."""

    async def test_concurrent_connections_10(self, test_client):
        """Test 10 concurrent WebSocket connections."""
        num_connections = 10
        websockets = []
        connection_times = []

        try:
            for i in range(num_connections):
                start = time.time()

                ws = test_client.websocket_connect(f"/ws/posture/perf-10-{i}")
                ws.__enter__()

                connection_time = time.time() - start
                connection_times.append(connection_time)

                websockets.append(ws)

                # Receive welcome
                ws.receive_json()

            # All should connect successfully
            assert len(websockets) == num_connections

            # Connection times should be reasonable
            avg_connection_time = statistics.mean(connection_times)
            assert avg_connection_time < 1.0  # Average < 1 second

        finally:
            for ws in websockets:
                ws.__exit__(None, None, None)

    async def test_concurrent_connections_50(self, test_client):
        """Test 50 concurrent WebSocket connections."""
        num_connections = 50
        websockets = []

        try:
            start = time.time()

            for i in range(num_connections):
                ws = test_client.websocket_connect(f"/ws/posture/perf-50-{i}")
                ws.__enter__()
                websockets.append(ws)
                ws.receive_json()

            elapsed = time.time() - start

            # All should connect
            assert len(websockets) == num_connections

            # Should complete in reasonable time (<10s)
            assert elapsed < 10.0

        finally:
            for ws in websockets:
                ws.__exit__(None, None, None)

    @pytest.mark.slow
    async def test_concurrent_connections_100(self, test_client):
        """Test 100 concurrent WebSocket connections (max capacity)."""
        num_connections = 100
        websockets = []
        successful_connections = 0

        try:
            for i in range(num_connections):
                try:
                    ws = test_client.websocket_connect(f"/ws/posture/perf-100-{i}")
                    ws.__enter__()
                    websockets.append(ws)
                    ws.receive_json()
                    successful_connections += 1
                except Exception as e:
                    # May hit max connections
                    pass

            # Should handle near max capacity
            assert successful_connections >= 95

        finally:
            for ws in websockets:
                try:
                    ws.__exit__(None, None, None)
                except:
                    pass

    async def test_message_latency(self, test_client, base64_encoded_frame):
        """Test message round-trip latency."""
        latencies = []

        with test_client.websocket_connect("/ws/posture/latency-test") as websocket:
            websocket.receive_json()  # Welcome

            # Measure latency for multiple messages
            for _ in range(30):
                start = time.time()

                # Send frame
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })

                # Receive analysis
                websocket.receive_json()

                latency = time.time() - start
                latencies.append(latency)

        # Calculate percentiles
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]

        # Assert performance requirements
        assert_performance_metrics(
            {
                "latency_p50": p50,
                "latency_p95": p95,
                "latency_p99": p99
            },
            max_latency_p95=0.5  # 500ms P95 latency
        )

        print(f"\nLatency - P50: {p50*1000:.1f}ms, P95: {p95*1000:.1f}ms, P99: {p99*1000:.1f}ms")

    async def test_frame_processing_throughput(self, test_client, base64_encoded_frame):
        """Test frame processing throughput (FPS)."""
        num_frames = 60  # 2 seconds worth at 30 FPS

        with test_client.websocket_connect("/ws/posture/throughput-test") as websocket:
            websocket.receive_json()  # Welcome

            start = time.time()

            # Send frames
            for i in range(num_frames):
                websocket.send_json({
                    "type": "frame",
                    "frame": base64_encoded_frame,
                    "exercise": "squat"
                })

            # Receive all responses
            for i in range(num_frames):
                websocket.receive_json()

            elapsed = time.time() - start
            fps = num_frames / elapsed

        # Assert minimum FPS
        assert_performance_metrics(
            {"fps": fps},
            min_fps=30.0  # Target 30+ FPS
        )

        print(f"\nThroughput: {fps:.1f} FPS")

    async def test_memory_usage_under_load(self, test_client, base64_encoded_frame):
        """Test memory usage during high load."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create multiple connections and send many frames
        websockets = []

        try:
            for i in range(10):
                ws = test_client.websocket_connect(f"/ws/posture/memory-{i}")
                ws.__enter__()
                websockets.append(ws)
                ws.receive_json()

            # Send 100 frames on each connection
            for ws in websockets:
                for _ in range(100):
                    ws.send_json({
                        "type": "frame",
                        "frame": base64_encoded_frame,
                        "exercise": "squat"
                    })

                    # Receive some responses
                    try:
                        ws.receive_json()
                    except:
                        pass

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable
            assert memory_increase < 500, f"Excessive memory usage: {memory_increase:.1f}MB"

            print(f"\nMemory increase: {memory_increase:.1f}MB")

        finally:
            for ws in websockets:
                ws.__exit__(None, None, None)

    async def test_ping_pong_latency(self, test_client):
        """Test ping/pong latency."""
        latencies = []

        with test_client.websocket_connect("/ws/posture/ping-latency") as websocket:
            websocket.receive_json()  # Welcome

            # Measure ping/pong latency
            for _ in range(50):
                start = time.time()

                websocket.send_json({"type": "ping"})
                response = websocket.receive_json()

                assert response["type"] == "pong"

                latency = time.time() - start
                latencies.append(latency)

        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)

        # Ping/pong should be very fast
        assert avg_latency < 0.05  # 50ms average
        assert max_latency < 0.2   # 200ms max

        print(f"\nPing/Pong - Avg: {avg_latency*1000:.1f}ms, Max: {max_latency*1000:.1f}ms")

    @pytest.mark.slow
    async def test_sustained_load(self, test_client, base64_encoded_frame):
        """Test sustained load over time."""
        duration_seconds = 30
        num_connections = 5

        websockets = []

        try:
            # Open connections
            for i in range(num_connections):
                ws = test_client.websocket_connect(f"/ws/posture/sustained-{i}")
                ws.__enter__()
                websockets.append(ws)
                ws.receive_json()

            # Send frames continuously
            start_time = time.time()
            frames_sent = 0

            while time.time() - start_time < duration_seconds:
                for ws in websockets:
                    ws.send_json({
                        "type": "frame",
                        "frame": base64_encoded_frame,
                        "exercise": "squat"
                    })
                    frames_sent += 1

                    # Try to receive (non-blocking)
                    try:
                        ws.receive_json()
                    except:
                        pass

                # Limit rate to ~30 FPS per connection
                await asyncio.sleep(1.0 / 30.0)

            elapsed = time.time() - start_time
            total_fps = frames_sent / elapsed

            print(f"\nSustained load: {total_fps:.1f} total FPS over {elapsed:.1f}s")

            # Should maintain throughput
            assert total_fps >= 100  # 5 connections * 20 FPS minimum

        finally:
            for ws in websockets:
                ws.__exit__(None, None, None)

    async def test_rapid_connect_disconnect(self, test_client):
        """Test rapid connection/disconnection cycles."""
        num_cycles = 50

        start = time.time()

        for i in range(num_cycles):
            with test_client.websocket_connect(f"/ws/posture/rapid-{i}") as websocket:
                websocket.receive_json()
                # Immediately disconnect

        elapsed = time.time() - start

        # Should complete quickly
        assert elapsed < 10.0

        print(f"\nRapid cycles: {num_cycles} in {elapsed:.1f}s ({num_cycles/elapsed:.1f} cycles/s)")


@pytest.mark.performance
class TestLoadScenarios:
    """Test realistic load scenarios."""

    async def test_typical_gym_load(self, test_client, base64_encoded_frame):
        """Simulate typical gym load (20 concurrent users)."""
        num_users = 20
        duration_seconds = 10

        websockets = []

        try:
            # Connect all users
            for i in range(num_users):
                ws = test_client.websocket_connect(f"/ws/posture/gym-user-{i}")
                ws.__enter__()
                websockets.append(ws)
                ws.receive_json()

            # Simulate workout (frames at 15 FPS per user)
            start_time = time.time()

            while time.time() - start_time < duration_seconds:
                for ws in websockets:
                    ws.send_json({
                        "type": "frame",
                        "frame": base64_encoded_frame,
                        "exercise": "squat"
                    })

                    try:
                        ws.receive_json()
                    except:
                        pass

                await asyncio.sleep(1.0 / 15.0)

            # All connections should still be active
            assert len(websockets) == num_users

        finally:
            for ws in websockets:
                ws.__exit__(None, None, None)

    async def test_peak_load(self, test_client, base64_encoded_frame):
        """Simulate peak load (50 concurrent users)."""
        num_users = 50
        duration_seconds = 5

        websockets = []
        successful = 0

        try:
            # Connect users
            for i in range(num_users):
                try:
                    ws = test_client.websocket_connect(f"/ws/posture/peak-user-{i}")
                    ws.__enter__()
                    websockets.append(ws)
                    ws.receive_json()
                    successful += 1
                except Exception as e:
                    pass

            # Should handle most connections
            assert successful >= num_users * 0.9  # 90% success rate

            # Brief load test
            start_time = time.time()

            while time.time() - start_time < duration_seconds:
                for ws in websockets:
                    try:
                        ws.send_json({
                            "type": "frame",
                            "frame": base64_encoded_frame,
                            "exercise": "squat"
                        })
                    except:
                        pass

                await asyncio.sleep(1.0 / 30.0)

        finally:
            for ws in websockets:
                try:
                    ws.__exit__(None, None, None)
                except:
                    pass
