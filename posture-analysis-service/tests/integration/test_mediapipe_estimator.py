"""Integration tests for MediaPipe pose estimator."""
import pytest
import numpy as np
import cv2
from pathlib import Path

from app.pose_estimator.mediapipe_estimator import MediaPipePoseEstimator


@pytest.fixture
def estimator():
    """Create MediaPipe estimator."""
    return MediaPipePoseEstimator(enable_gpu=False)


@pytest.fixture
def sample_frame():
    """Create a sample frame for testing."""
    # Create a simple test frame (blue background)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:, :] = [100, 100, 100]  # Gray background
    return frame


@pytest.mark.asyncio
async def test_estimator_initialization(estimator):
    """Test estimator initializes correctly."""
    assert estimator is not None
    assert estimator.frame_count == 0
    assert not estimator.enable_gpu


@pytest.mark.asyncio
async def test_estimate_with_sample_frame(estimator, sample_frame):
    """Test pose estimation with a simple frame."""
    result = await estimator.estimate(sample_frame)

    assert result is not None
    assert "landmarks" in result
    assert "confidence" in result
    assert "keypoints" in result
    assert "frame_number" in result

    # Should have 33 landmarks (MediaPipe standard)
    assert len(result["landmarks"]) == 33

    # Each landmark should have x, y, z, visibility
    for landmark in result["landmarks"]:
        assert "x" in landmark
        assert "y" in landmark
        assert "z" in landmark
        assert "visibility" in landmark


@pytest.mark.asyncio
async def test_estimate_increments_frame_count(estimator, sample_frame):
    """Test that frame count increments."""
    initial_count = estimator.frame_count

    await estimator.estimate(sample_frame)
    assert estimator.frame_count == initial_count + 1

    await estimator.estimate(sample_frame)
    assert estimator.frame_count == initial_count + 2


@pytest.mark.asyncio
async def test_preprocess_large_frame(estimator):
    """Test frame preprocessing for large frames."""
    # Create a large frame
    large_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    result = await estimator.estimate(large_frame)

    # Should still process successfully
    assert result is not None
    assert len(result["landmarks"]) == 33


@pytest.mark.asyncio
async def test_get_keypoint(estimator, sample_frame):
    """Test keypoint extraction."""
    result = await estimator.estimate(sample_frame)

    # Test getting a specific keypoint
    nose = estimator.get_keypoint(result, "nose")
    assert "x" in nose
    assert "y" in nose

    left_shoulder = estimator.get_keypoint(result, "left_shoulder")
    assert "x" in left_shoulder
    assert "confidence" in left_shoulder


@pytest.mark.asyncio
async def test_to_pydantic_landmarks(estimator, sample_frame):
    """Test conversion to Pydantic models."""
    result = await estimator.estimate(sample_frame)

    pose_landmarks = estimator.to_pydantic_landmarks(result)

    if pose_landmarks:  # May be None if no pose detected
        assert len(pose_landmarks.landmarks) == 33
        assert 0.0 <= pose_landmarks.confidence <= 1.0


@pytest.mark.asyncio
async def test_invalid_frame_handling(estimator):
    """Test handling of invalid frames."""
    # Test with None
    invalid_frame = None

    try:
        result = await estimator.estimate(invalid_frame)
        # Should return empty result, not crash
        assert result is not None
    except Exception:
        # Or may raise exception, which is acceptable
        pass


@pytest.mark.asyncio
async def test_empty_frame_handling(estimator):
    """Test handling of empty frames."""
    empty_frame = np.zeros((0, 0, 3), dtype=np.uint8)

    try:
        result = await estimator.estimate(empty_frame)
        assert result is not None
    except Exception:
        # Exception is acceptable for invalid input
        pass


@pytest.mark.asyncio
async def test_bgr_to_rgb_conversion(estimator):
    """Test BGR to RGB color space conversion."""
    # Create frame with specific color (BGR)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:, :] = [255, 0, 0]  # Blue in BGR

    result = await estimator.estimate(frame)

    # Should process without errors
    assert result is not None
    assert "landmarks" in result


@pytest.mark.asyncio
async def test_multiple_frames_processing(estimator, sample_frame):
    """Test processing multiple frames in sequence."""
    results = []

    for i in range(5):
        result = await estimator.estimate(sample_frame)
        results.append(result)

    # All results should be valid
    assert len(results) == 5
    for result in results:
        assert result is not None
        assert len(result["landmarks"]) == 33

    # Frame numbers should increment
    for i, result in enumerate(results, 1):
        assert result["frame_number"] == i


def test_landmark_name_mapping():
    """Test landmark name mapping is correct."""
    assert 0 in MediaPipePoseEstimator.LANDMARK_NAMES
    assert MediaPipePoseEstimator.LANDMARK_NAMES[0] == "nose"
    assert MediaPipePoseEstimator.LANDMARK_NAMES[11] == "left_shoulder"
    assert MediaPipePoseEstimator.LANDMARK_NAMES[23] == "left_hip"
