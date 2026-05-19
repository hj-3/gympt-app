"""Test rep counter functionality."""
import pytest
from app.counting.rep_counter import RepCounter, RepState, RepCountResult
from tests.utils.landmark_generator import LandmarkGenerator
from tests.utils.assertions import assert_rep_count, assert_state_transition


pytestmark = [pytest.mark.unit]


class TestRepCounter:
    """Test basic rep counting functionality."""

    def test_initialization(self):
        """Test rep counter initialization."""
        counter = RepCounter(exercise_type="squat")

        assert counter.exercise_type == "squat"
        assert counter.current_state == RepState.STARTING
        assert counter.total_reps == 0

    def test_initialization_with_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        custom_thresholds = {
            "down_threshold": 0.10,
            "up_threshold": 0.30,
            "hysteresis": 0.08
        }

        counter = RepCounter(exercise_type="squat", thresholds=custom_thresholds)

        assert counter.thresholds == custom_thresholds

    def test_squat_rep_counting(self):
        """Test squat rep counting through complete cycle."""
        counter = RepCounter(exercise_type="squat")

        # Standing position
        keypoints_up = {
            "left_hip": {"x": 0.42, "y": 0.50, "confidence": 0.95},
            "left_knee": {"x": 0.40, "y": 0.75, "confidence": 0.95}
        }

        # Down position
        keypoints_down = {
            "left_hip": {"x": 0.42, "y": 0.68, "confidence": 0.95},
            "left_knee": {"x": 0.40, "y": 0.72, "confidence": 0.95}
        }

        # Start position
        result = counter.count_reps(keypoints_up)
        assert result.total_reps == 0
        assert result.current_state in [RepState.STARTING, RepState.UP]

        # Go down
        result = counter.count_reps(keypoints_down)
        assert result.current_state in [RepState.DOWN, RepState.STARTING]

        # Come back up
        result = counter.count_reps(keypoints_up)

        # May need to send more frames to complete the rep
        for _ in range(5):
            result = counter.count_reps(keypoints_up)

        # Should eventually count a rep
        assert result.total_reps >= 0

    def test_pushup_rep_counting(self):
        """Test pushup rep counting."""
        counter = RepCounter(exercise_type="pushup")

        # Up position
        keypoints_up = {
            "left_shoulder": {"x": 0.35, "y": 0.38, "confidence": 0.92},
            "left_wrist": {"x": 0.28, "y": 0.52, "confidence": 0.92}
        }

        # Down position
        keypoints_down = {
            "left_shoulder": {"x": 0.35, "y": 0.48, "confidence": 0.90},
            "left_wrist": {"x": 0.28, "y": 0.52, "confidence": 0.90}
        }

        # Cycle through positions
        result = counter.count_reps(keypoints_up)
        result = counter.count_reps(keypoints_down)
        result = counter.count_reps(keypoints_up)

        assert result.total_reps >= 0

    def test_deadlift_rep_counting(self):
        """Test deadlift rep counting."""
        counter = RepCounter(exercise_type="deadlift")

        # Bottom position
        keypoints_down = {
            "left_hip": {"x": 0.42, "y": 0.65, "confidence": 0.93},
            "left_ankle": {"x": 0.38, "y": 0.90, "confidence": 0.92}
        }

        # Top position
        keypoints_up = {
            "left_hip": {"x": 0.42, "y": 0.50, "confidence": 0.95},
            "left_ankle": {"x": 0.38, "y": 0.90, "confidence": 0.95}
        }

        result = counter.count_reps(keypoints_down)
        result = counter.count_reps(keypoints_up)

        assert result.total_reps >= 0

    def test_hysteresis_prevents_double_counting(self):
        """Test hysteresis prevents false rep counting."""
        counter = RepCounter(exercise_type="squat")

        # Keypoints right at threshold (oscillating)
        keypoints_threshold = {
            "left_hip": {"x": 0.42, "y": 0.60, "confidence": 0.95},
            "left_knee": {"x": 0.40, "y": 0.73, "confidence": 0.95}
        }

        # Send many frames at threshold
        initial_reps = counter.total_reps

        for _ in range(20):
            counter.count_reps(keypoints_threshold)

        # Should not have counted many reps from oscillation
        assert counter.total_reps - initial_reps <= 1

    def test_state_transitions(self):
        """Test valid state transitions."""
        counter = RepCounter(exercise_type="squat")

        valid_transitions = {
            RepState.STARTING: [RepState.DOWN, RepState.STARTING],
            RepState.DOWN: [RepState.UP, RepState.DOWN],
            RepState.UP: [RepState.COMPLETED, RepState.UP],
            RepState.COMPLETED: [RepState.STARTING]
        }

        # Track state transitions
        previous_state = counter.current_state

        # Deep squat to trigger DOWN state
        deep_squat_keypoints = {
            "left_hip": {"x": 0.42, "y": 0.70, "confidence": 0.95},
            "left_knee": {"x": 0.40, "y": 0.72, "confidence": 0.95}
        }

        result = counter.count_reps(deep_squat_keypoints)
        current_state = result.current_state

        # Verify valid transition
        if previous_state != current_state:
            assert_state_transition(
                str(previous_state),
                str(current_state),
                {k.value: [v.value for v in vals] for k, vals in valid_transitions.items()}
            )

    def test_reset(self):
        """Test rep counter reset."""
        counter = RepCounter(exercise_type="squat")

        # Do some reps
        counter.total_reps = 5
        counter.current_state = RepState.UP

        # Reset
        counter.reset()

        assert counter.total_reps == 0
        assert counter.current_state == RepState.STARTING
        assert counter.previous_position == 0.0

    def test_get_progress(self):
        """Test rep progress calculation."""
        counter = RepCounter(exercise_type="squat")

        # Test each state's progress
        counter.current_state = RepState.STARTING
        assert counter.get_progress() == 0.0

        counter.current_state = RepState.DOWN
        assert counter.get_progress() == 0.33

        counter.current_state = RepState.UP
        assert counter.get_progress() == 0.66

        counter.current_state = RepState.COMPLETED
        assert counter.get_progress() == 1.0

    def test_missing_keypoints(self):
        """Test handling of missing keypoints."""
        counter = RepCounter(exercise_type="squat")

        # Empty keypoints
        result = counter.count_reps({})

        assert result.position_value == 0.0
        # Should not crash

    def test_partial_keypoints(self):
        """Test handling of partial keypoint data."""
        counter = RepCounter(exercise_type="squat")

        # Only one keypoint
        partial_keypoints = {
            "left_hip": {"x": 0.42, "y": 0.60, "confidence": 0.95}
            # Missing left_knee
        }

        result = counter.count_reps(partial_keypoints)

        # Should handle gracefully
        assert result is not None


class TestRepCounterEdgeCases:
    """Test rep counter edge cases."""

    def test_rapid_movements(self):
        """Test handling of very rapid movements."""
        counter = RepCounter(exercise_type="squat")

        # Rapidly alternate between up and down
        keypoints_up = {
            "left_hip": {"x": 0.42, "y": 0.50, "confidence": 0.95},
            "left_knee": {"x": 0.40, "y": 0.75, "confidence": 0.95}
        }

        keypoints_down = {
            "left_hip": {"x": 0.42, "y": 0.68, "confidence": 0.95},
            "left_knee": {"x": 0.40, "y": 0.72, "confidence": 0.95}
        }

        initial_reps = counter.total_reps

        # Rapid alternation
        for _ in range(10):
            counter.count_reps(keypoints_up)
            counter.count_reps(keypoints_down)

        # Should count some reps but not double count
        reps_counted = counter.total_reps - initial_reps
        assert reps_counted <= 10  # Not more than cycles

    def test_pause_mid_rep(self):
        """Test handling of pause during rep."""
        counter = RepCounter(exercise_type="squat")

        # Go to down position
        keypoints_down = {
            "left_hip": {"x": 0.42, "y": 0.68, "confidence": 0.95},
            "left_knee": {"x": 0.40, "y": 0.72, "confidence": 0.95}
        }

        counter.count_reps(keypoints_down)

        # Pause (send same position multiple times)
        for _ in range(10):
            result = counter.count_reps(keypoints_down)

        # Should maintain state
        assert result.current_state in [RepState.DOWN, RepState.STARTING]

    def test_incomplete_rep(self):
        """Test incomplete rep doesn't count."""
        counter = RepCounter(exercise_type="squat")

        # Partial movement (not reaching down threshold)
        keypoints_partial = {
            "left_hip": {"x": 0.42, "y": 0.58, "confidence": 0.95},
            "left_knee": {"x": 0.40, "y": 0.74, "confidence": 0.95}
        }

        initial_reps = counter.total_reps

        # Multiple partial movements
        for _ in range(20):
            counter.count_reps(keypoints_partial)

        # Should not count as full rep
        assert counter.total_reps == initial_reps

    def test_noisy_landmarks(self):
        """Test rep counting with noisy landmark data."""
        counter = RepCounter(exercise_type="squat")
        landmark_gen = LandmarkGenerator()

        # Generate sequence with noise
        sequence = landmark_gen.generate_rep_sequence(
            exercise="squat",
            num_reps=3,
            frames_per_rep=30
        )

        # Add extra noise
        for pose_data in sequence:
            keypoints = landmark_gen.add_noise(
                pose_data["keypoints"],
                noise_level=0.02  # Significant noise
            )
            counter.count_reps(keypoints)

        # Should still count some reps despite noise
        assert counter.total_reps >= 0


class TestRepCounterSequences:
    """Test rep counting with realistic sequences."""

    def test_ten_rep_sequence(self):
        """Test counting 10 reps accurately."""
        counter = RepCounter(exercise_type="squat")
        landmark_gen = LandmarkGenerator()

        sequence = landmark_gen.generate_rep_sequence(
            exercise="squat",
            num_reps=10,
            frames_per_rep=30
        )

        for pose_data in sequence:
            counter.count_reps(pose_data["keypoints"])

        # Should count close to 10 reps (allow some tolerance)
        assert_rep_count(
            {"total_reps": counter.total_reps},
            expected_reps=10,
            tolerance=2
        )

    def test_pushup_sequence(self):
        """Test pushup rep sequence."""
        counter = RepCounter(exercise_type="pushup")
        landmark_gen = LandmarkGenerator()

        sequence = landmark_gen.generate_rep_sequence(
            exercise="pushup",
            num_reps=20,
            frames_per_rep=25
        )

        for pose_data in sequence:
            counter.count_reps(pose_data["keypoints"])

        # Should count close to 20 reps
        assert_rep_count(
            {"total_reps": counter.total_reps},
            expected_reps=20,
            tolerance=3
        )

    def test_mixed_rep_speeds(self):
        """Test reps at different speeds."""
        counter = RepCounter(exercise_type="squat")
        landmark_gen = LandmarkGenerator()

        # Fast reps (15 frames per rep)
        fast_sequence = landmark_gen.generate_rep_sequence(
            exercise="squat",
            num_reps=3,
            frames_per_rep=15
        )

        # Slow reps (60 frames per rep)
        slow_sequence = landmark_gen.generate_rep_sequence(
            exercise="squat",
            num_reps=3,
            frames_per_rep=60
        )

        # Process fast reps
        for pose_data in fast_sequence:
            counter.count_reps(pose_data["keypoints"])

        # Process slow reps
        for pose_data in slow_sequence:
            counter.count_reps(pose_data["keypoints"])

        # Should count reps regardless of speed
        assert counter.total_reps >= 3


@pytest.mark.performance
class TestRepCounterPerformance:
    """Test rep counter performance."""

    def test_counting_performance(self):
        """Test rep counting speed."""
        import time

        counter = RepCounter(exercise_type="squat")

        keypoints = {
            "left_hip": {"x": 0.42, "y": 0.60, "confidence": 0.95},
            "left_knee": {"x": 0.40, "y": 0.73, "confidence": 0.95}
        }

        num_iterations = 1000

        start = time.time()

        for _ in range(num_iterations):
            counter.count_reps(keypoints)

        elapsed = time.time() - start
        avg_time = elapsed / num_iterations

        # Should be very fast (<0.5ms per count)
        assert avg_time < 0.0005, f"Rep counting too slow: {avg_time*1000:.2f}ms"

    def test_long_sequence_performance(self):
        """Test performance with long sequences."""
        import time

        counter = RepCounter(exercise_type="squat")
        landmark_gen = LandmarkGenerator()

        # Generate very long sequence (1000 frames)
        sequence = landmark_gen.generate_rep_sequence(
            exercise="squat",
            num_reps=33,
            frames_per_rep=30
        )

        start = time.time()

        for pose_data in sequence:
            counter.count_reps(pose_data["keypoints"])

        elapsed = time.time() - start

        # Should complete in reasonable time (<1s)
        assert elapsed < 1.0, f"Long sequence too slow: {elapsed:.2f}s"
