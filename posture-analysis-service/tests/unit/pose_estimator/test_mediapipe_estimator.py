"""Test MediaPipe pose estimator."""
import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock

from app.pose_estimator.mediapipe_estimator import MediaPipePoseEstimator
from tests.utils.assertions import assert_landmarks_valid, assert_confidence_threshold


pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestMediaPipeEstimator:
    """Test MediaPipe pose estimation."""

    @pytest.fixture
    def estimator(self):
        """Create MediaPipe estimator instance."""
        return MediaPipePoseEstimator(enable_gpu=False)

    async def test_estimator_initialization(self, estimator):
        """Test estimator initializes correctly."""
        assert estimator is not None
        assert hasattr(estimator, 'estimate')
        assert hasattr(estimator, 'get_keypoint')

    async def test_estimate_with_valid_frame(self, estimator, sample_frame_480p):
        """Test pose estimation with valid frame."""
        result = await estimator.estimate(sample_frame_480p)

        assert result is not None
        assert "keypoints" in result
        assert "confidence" in result
        assert "landmarks" in result

    async def test_estimate_with_different_resolutions(self, estimator):
        """Test pose estimation with various resolutions."""
        resolutions = [
            (480, 640, 3),   # 480p
            (720, 1280, 3),  # 720p
            (1080, 1920, 3)  # 1080p
        ]

        for resolution in resolutions:
            frame = np.random.randint(0, 255, resolution, dtype=np.uint8)
            result = await estimator.estimate(frame)

            assert result is not None
            assert "keypoints" in result

    async def test_estimate_with_corrupted_frame(self, estimator):
        """Test handling of corrupted frame data."""
        # Empty frame
        empty_frame = np.array([])

        result = await estimator.estimate(empty_frame)

        # Should handle gracefully (return empty or error)
        assert result is not None

    async def test_estimate_with_wrong_format(self, estimator):
        """Test handling of wrong frame format."""
        # Wrong shape (missing color channels)
        wrong_frame = np.random.randint(0, 255, (480, 640), dtype=np.uint8)

        result = await estimator.estimate(wrong_frame)

        # Should handle gracefully
        assert result is not None

    async def test_landmark_visibility_thresholds(self, estimator, sample_frame_480p):
        """Test landmark visibility filtering."""
        result = await estimator.estimate(sample_frame_480p)

        keypoints = result.get("keypoints", {})

        # All returned keypoints should have confidence scores
        for name, point in keypoints.items():
            assert "confidence" in point
            # Confidence should be valid (0-1)
            assert 0 <= point["confidence"] <= 1

    async def test_cpu_mode(self):
        """Test estimator in CPU mode."""
        estimator = MediaPipeEstimator(use_gpu=False)

        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = await estimator.estimate(frame)

        assert result is not None

    @pytest.mark.gpu
    async def test_gpu_mode(self):
        """Test estimator in GPU mode (skip if no GPU)."""
        try:
            import torch
            if not torch.cuda.is_available():
                pytest.skip("GPU not available")

            estimator = MediaPipeEstimator(use_gpu=True)

            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            result = await estimator.estimate(frame)

            assert result is not None
        except ImportError:
            pytest.skip("PyTorch not installed")

    async def test_get_keypoint(self, estimator, mock_mediapipe_landmarks):
        """Test get_keypoint method."""
        # Mock landmarks
        keypoint = estimator.get_keypoint(mock_mediapipe_landmarks, "left_shoulder")

        assert keypoint is not None
        assert "x" in keypoint
        assert "y" in keypoint

    async def test_calculate_angle(self, estimator):
        """Test angle calculation between three points."""
        # Right angle (90 degrees)
        point1 = {"x": 0.0, "y": 0.0}
        point2 = {"x": 1.0, "y": 0.0}
        point3 = {"x": 1.0, "y": 1.0}

        angle = estimator.calculate_angle(point1, point2, point3)

        # Should be approximately 90 degrees
        assert 85 <= angle <= 95

    async def test_consecutive_estimates(self, estimator, sample_frame_480p):
        """Test multiple consecutive estimates."""
        results = []

        for _ in range(10):
            result = await estimator.estimate(sample_frame_480p)
            results.append(result)

        # All should succeed
        assert len(results) == 10
        assert all(r is not None for r in results)

    @pytest.mark.performance
    async def test_processing_speed(self, estimator, sample_frame_480p):
        """Test pose estimation processing speed."""
        import time

        num_frames = 30
        start_time = time.time()

        for _ in range(num_frames):
            await estimator.estimate(sample_frame_480p)

        elapsed = time.time() - start_time
        fps = num_frames / elapsed

        # Should achieve at least 15 FPS on CPU
        assert fps >= 15, f"FPS too low: {fps:.1f}"

    @pytest.mark.performance
    async def test_memory_usage(self, estimator, sample_frame_480p):
        """Test memory usage doesn't leak."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process many frames
        for _ in range(100):
            await estimator.estimate(sample_frame_480p)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (<500MB)
        assert memory_increase < 500, f"Memory leak detected: {memory_increase:.1f}MB increase"

    async def test_black_frame(self, estimator):
        """Test estimation with black frame (no person)."""
        black_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = await estimator.estimate(black_frame)

        # Should handle gracefully (no landmarks or low confidence)
        assert result is not None
        # Confidence might be low or keypoints empty

    async def test_noise_frame(self, estimator):
        """Test estimation with noisy frame."""
        noise_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        result = await estimator.estimate(noise_frame)

        # Should handle gracefully
        assert result is not None


@pytest.mark.integration
class TestMediaPipeEstimatorIntegration:
    """Integration tests with actual MediaPipe library."""

    @pytest.fixture
    def estimator(self):
        """Create MediaPipe estimator."""
        return MediaPipeEstimator(use_gpu=False)

    async def test_with_mock_mediapipe(self, sample_frame_480p):
        """Test with mocked MediaPipe library."""
        with patch('mediapipe.solutions.pose.Pose') as mock_pose_class:
            # Mock MediaPipe Pose
            mock_pose = MagicMock()
            mock_pose_class.return_value = mock_pose

            # Mock process result
            mock_result = MagicMock()
            mock_result.pose_landmarks = None  # No person detected
            mock_pose.process.return_value = mock_result

            estimator = MediaPipeEstimator(use_gpu=False)
            result = await estimator.estimate(sample_frame_480p)

            assert result is not None
            mock_pose.process.assert_called_once()
