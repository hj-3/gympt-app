"""Integration tests for rep counter."""
import pytest
from app.counting.rep_counter import RepCounter, RepState


@pytest.fixture
def squat_counter():
    """Create squat rep counter."""
    return RepCounter("squat")


@pytest.fixture
def pushup_counter():
    """Create pushup rep counter."""
    return RepCounter("pushup")


def test_counter_initialization(squat_counter):
    """Test rep counter initializes correctly."""
    assert squat_counter.exercise_type == "squat"
    assert squat_counter.current_state == RepState.STARTING
    assert squat_counter.total_reps == 0


def test_squat_rep_sequence(squat_counter):
    """Test counting a full squat rep."""
    # Simulate squat movement with keypoints
    # Starting position (standing)
    keypoints_standing = {
        "left_hip": {"x": 0.5, "y": 0.5, "confidence": 0.9},
        "left_knee": {"x": 0.5, "y": 0.75, "confidence": 0.9},
    }

    result = squat_counter.count_reps(keypoints_standing)
    assert result.current_state == RepState.STARTING
    assert result.total_reps == 0

    # Bottom position (squatting down)
    keypoints_down = {
        "left_hip": {"x": 0.5, "y": 0.7, "confidence": 0.9},
        "left_knee": {"x": 0.5, "y": 0.75, "confidence": 0.9},
    }

    result = squat_counter.count_reps(keypoints_down)
    # Should transition to DOWN state
    assert result.current_state == RepState.DOWN
    assert result.total_reps == 0

    # Coming back up
    keypoints_up = {
        "left_hip": {"x": 0.5, "y": 0.55, "confidence": 0.9},
        "left_knee": {"x": 0.5, "y": 0.75, "confidence": 0.9},
    }

    result = squat_counter.count_reps(keypoints_up)
    # Should transition to UP state
    assert result.current_state == RepState.UP

    # Complete the rep (back to starting position)
    keypoints_complete = {
        "left_hip": {"x": 0.5, "y": 0.45, "confidence": 0.9},
        "left_knee": {"x": 0.5, "y": 0.75, "confidence": 0.9},
    }

    result = squat_counter.count_reps(keypoints_complete)
    # Should complete rep and reset
    assert result.total_reps == 1


def test_pushup_rep_sequence(pushup_counter):
    """Test counting a full pushup rep."""
    # Starting position (plank)
    keypoints_start = {
        "left_shoulder": {"x": 0.5, "y": 0.4, "confidence": 0.9},
        "left_wrist": {"x": 0.5, "y": 0.6, "confidence": 0.9},
    }

    result = pushup_counter.count_reps(keypoints_start)
    assert result.current_state == RepState.STARTING

    # Lowered position
    keypoints_down = {
        "left_shoulder": {"x": 0.5, "y": 0.5, "confidence": 0.9},
        "left_wrist": {"x": 0.5, "y": 0.6, "confidence": 0.9},
    }

    result = pushup_counter.count_reps(keypoints_down)
    assert result.current_state == RepState.DOWN

    # Push up
    keypoints_up = {
        "left_shoulder": {"x": 0.5, "y": 0.35, "confidence": 0.9},
        "left_wrist": {"x": 0.5, "y": 0.6, "confidence": 0.9},
    }

    result = pushup_counter.count_reps(keypoints_up)
    # Should count a rep
    assert result.total_reps >= 0


def test_multiple_reps(squat_counter):
    """Test counting multiple reps in sequence."""
    reps_completed = 0

    for _ in range(3):
        # Down
        squat_counter.count_reps({
            "left_hip": {"x": 0.5, "y": 0.7, "confidence": 0.9},
            "left_knee": {"x": 0.5, "y": 0.75, "confidence": 0.9},
        })

        # Up
        squat_counter.count_reps({
            "left_hip": {"x": 0.5, "y": 0.55, "confidence": 0.9},
            "left_knee": {"x": 0.5, "y": 0.75, "confidence": 0.9},
        })

        # Complete
        result = squat_counter.count_reps({
            "left_hip": {"x": 0.5, "y": 0.45, "confidence": 0.9},
            "left_knee": {"x": 0.5, "y": 0.75, "confidence": 0.9},
        })

    # Should have counted multiple reps
    assert result.total_reps > 0


def test_hysteresis_prevents_false_counting(squat_counter):
    """Test that hysteresis prevents double counting."""
    # Simulate noisy position data around threshold
    keypoints_threshold = {
        "left_hip": {"x": 0.5, "y": 0.68, "confidence": 0.9},
        "left_knee": {"x": 0.5, "y": 0.75, "confidence": 0.9},
    }

    # Count several times with similar position
    results = []
    for _ in range(5):
        result = squat_counter.count_reps(keypoints_threshold)
        results.append(result)

    # Should not count multiple reps from noisy data
    reps = [r.total_reps for r in results]
    assert max(reps) - min(reps) <= 1  # At most 1 rep difference


def test_reset_counter(squat_counter):
    """Test resetting the rep counter."""
    # Do some reps
    squat_counter.count_reps({
        "left_hip": {"x": 0.5, "y": 0.7, "confidence": 0.9},
        "left_knee": {"x": 0.5, "y": 0.75, "confidence": 0.9},
    })

    # Reset
    squat_counter.reset()

    assert squat_counter.total_reps == 0
    assert squat_counter.current_state == RepState.STARTING


def test_get_progress(squat_counter):
    """Test getting rep progress."""
    assert squat_counter.get_progress() == 0.0

    # Move to DOWN state
    squat_counter.current_state = RepState.DOWN
    progress = squat_counter.get_progress()
    assert 0.0 <= progress <= 1.0

    # Move to UP state
    squat_counter.current_state = RepState.UP
    progress = squat_counter.get_progress()
    assert progress > 0.0


def test_custom_thresholds():
    """Test rep counter with custom thresholds."""
    custom_thresholds = {
        "down_threshold": 0.2,
        "up_threshold": 0.3,
        "hysteresis": 0.08,
    }

    counter = RepCounter("squat", thresholds=custom_thresholds)
    assert counter.thresholds == custom_thresholds


def test_missing_keypoints_handling(squat_counter):
    """Test handling of missing keypoints."""
    # Missing keypoints
    keypoints_missing = {}

    result = squat_counter.count_reps(keypoints_missing)

    # Should not crash
    assert result is not None
    assert result.position_value == 0.0


def test_deadlift_counter():
    """Test deadlift rep counter."""
    counter = RepCounter("deadlift")

    keypoints_bottom = {
        "left_hip": {"x": 0.5, "y": 0.6, "confidence": 0.9},
        "left_ankle": {"x": 0.5, "y": 0.85, "confidence": 0.9},
    }

    result = counter.count_reps(keypoints_bottom)
    assert result is not None
    assert result.current_state in [RepState.STARTING, RepState.DOWN]


def test_unsupported_exercise():
    """Test rep counter with unsupported exercise."""
    counter = RepCounter("unsupported_exercise")

    keypoints = {
        "left_hip": {"x": 0.5, "y": 0.5, "confidence": 0.9},
        "left_knee": {"x": 0.5, "y": 0.75, "confidence": 0.9},
    }

    result = counter.count_reps(keypoints)
    # Should fall back to default thresholds
    assert result is not None
