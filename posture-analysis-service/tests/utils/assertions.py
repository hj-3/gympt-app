"""Custom assertions for posture analysis testing."""
from typing import Dict, Any, List, Optional


def assert_rep_count(
    result: Dict[str, Any],
    expected_reps: int,
    tolerance: int = 0
):
    """
    Assert rep count is within tolerance.

    Args:
        result: Rep counting result
        expected_reps: Expected number of reps
        tolerance: Allowed difference
    """
    actual_reps = result.get("total_reps", result.get("current_reps", 0))
    diff = abs(actual_reps - expected_reps)

    assert diff <= tolerance, (
        f"Rep count mismatch: expected {expected_reps} "
        f"(±{tolerance}), got {actual_reps}"
    )


def assert_score_in_range(
    analysis: Dict[str, Any],
    min_score: float,
    max_score: float
):
    """
    Assert posture score is within range.

    Args:
        analysis: Analysis result
        min_score: Minimum acceptable score
        max_score: Maximum acceptable score
    """
    score = analysis.get("score", 0.0)

    assert min_score <= score <= max_score, (
        f"Score out of range: expected [{min_score}, {max_score}], "
        f"got {score}"
    )


def assert_landmarks_valid(
    pose_data: Dict[str, Any],
    required_keypoints: Optional[List[str]] = None
):
    """
    Assert pose landmarks are valid.

    Args:
        pose_data: Pose estimation data
        required_keypoints: List of required keypoint names
    """
    keypoints = pose_data.get("keypoints", {})

    assert keypoints, "No keypoints found in pose data"

    if required_keypoints:
        missing_keypoints = [
            kp for kp in required_keypoints
            if kp not in keypoints
        ]

        assert not missing_keypoints, (
            f"Missing required keypoints: {missing_keypoints}"
        )

    # Validate keypoint structure
    for name, point in keypoints.items():
        assert "x" in point, f"Keypoint {name} missing 'x' coordinate"
        assert "y" in point, f"Keypoint {name} missing 'y' coordinate"
        assert "confidence" in point, f"Keypoint {name} missing confidence"

        # Validate coordinate ranges
        assert 0 <= point["x"] <= 1, (
            f"Keypoint {name} x coordinate out of range: {point['x']}"
        )
        assert 0 <= point["y"] <= 1, (
            f"Keypoint {name} y coordinate out of range: {point['y']}"
        )
        assert 0 <= point["confidence"] <= 1, (
            f"Keypoint {name} confidence out of range: {point['confidence']}"
        )


def assert_analysis_complete(analysis: Dict[str, Any]):
    """
    Assert analysis result is complete.

    Args:
        analysis: Analysis result
    """
    required_fields = ["score", "issues"]

    for field in required_fields:
        assert field in analysis, f"Analysis missing required field: {field}"

    assert isinstance(analysis["score"], (int, float)), (
        f"Score must be numeric, got {type(analysis['score'])}"
    )

    assert isinstance(analysis["issues"], list), (
        f"Issues must be a list, got {type(analysis['issues'])}"
    )


def assert_websocket_message(
    message: Dict[str, Any],
    expected_type: str,
    required_fields: Optional[List[str]] = None
):
    """
    Assert WebSocket message structure.

    Args:
        message: Received message
        expected_type: Expected message type
        required_fields: List of required fields
    """
    assert "type" in message, "Message missing 'type' field"

    assert message["type"] == expected_type, (
        f"Message type mismatch: expected '{expected_type}', "
        f"got '{message['type']}'"
    )

    if required_fields:
        missing_fields = [
            field for field in required_fields
            if field not in message
        ]

        assert not missing_fields, (
            f"Message missing required fields: {missing_fields}"
        )


def assert_form_issues_detected(
    analysis: Dict[str, Any],
    expected_issues: List[str],
    exact_match: bool = False
):
    """
    Assert specific form issues are detected.

    Args:
        analysis: Analysis result
        expected_issues: List of expected issue names
        exact_match: If True, require exact match; if False, require subset
    """
    detected_issues = analysis.get("issues", [])

    if exact_match:
        assert set(detected_issues) == set(expected_issues), (
            f"Form issues don't match exactly: "
            f"expected {expected_issues}, got {detected_issues}"
        )
    else:
        missing_issues = [
            issue for issue in expected_issues
            if issue not in detected_issues
        ]

        assert not missing_issues, (
            f"Missing expected form issues: {missing_issues}"
        )


def assert_session_metrics(
    session_data: Dict[str, Any],
    min_reps: Optional[int] = None,
    min_score: Optional[float] = None,
    min_duration: Optional[float] = None
):
    """
    Assert session metrics meet minimum requirements.

    Args:
        session_data: Session data
        min_reps: Minimum rep count
        min_score: Minimum average score
        min_duration: Minimum duration in seconds
    """
    if min_reps is not None:
        actual_reps = session_data.get("total_reps", 0)
        assert actual_reps >= min_reps, (
            f"Session reps below minimum: expected >={min_reps}, "
            f"got {actual_reps}"
        )

    if min_score is not None:
        actual_score = session_data.get("average_score", 0.0)
        assert actual_score >= min_score, (
            f"Session score below minimum: expected >={min_score}, "
            f"got {actual_score}"
        )

    if min_duration is not None:
        actual_duration = session_data.get("duration_seconds", 0.0)
        assert actual_duration >= min_duration, (
            f"Session duration below minimum: expected >={min_duration}s, "
            f"got {actual_duration}s"
        )


def assert_performance_metrics(
    metrics: Dict[str, Any],
    max_latency_p95: Optional[float] = None,
    min_fps: Optional[float] = None,
    max_memory_mb: Optional[float] = None
):
    """
    Assert performance metrics meet requirements.

    Args:
        metrics: Performance metrics
        max_latency_p95: Maximum P95 latency in seconds
        min_fps: Minimum FPS
        max_memory_mb: Maximum memory usage in MB
    """
    if max_latency_p95 is not None:
        actual_latency = metrics.get("latency_p95", float('inf'))
        assert actual_latency <= max_latency_p95, (
            f"P95 latency too high: expected <={max_latency_p95}s, "
            f"got {actual_latency}s"
        )

    if min_fps is not None:
        actual_fps = metrics.get("fps", 0.0)
        assert actual_fps >= min_fps, (
            f"FPS too low: expected >={min_fps}, got {actual_fps}"
        )

    if max_memory_mb is not None:
        actual_memory = metrics.get("memory_mb", float('inf'))
        assert actual_memory <= max_memory_mb, (
            f"Memory usage too high: expected <={max_memory_mb}MB, "
            f"got {actual_memory}MB"
        )


def assert_confidence_threshold(
    pose_data: Dict[str, Any],
    min_confidence: float = 0.7
):
    """
    Assert pose estimation confidence meets threshold.

    Args:
        pose_data: Pose estimation data
        min_confidence: Minimum confidence threshold
    """
    confidence = pose_data.get("confidence", 0.0)

    assert confidence >= min_confidence, (
        f"Pose confidence below threshold: expected >={min_confidence}, "
        f"got {confidence}"
    )


def assert_state_transition(
    previous_state: str,
    current_state: str,
    valid_transitions: Dict[str, List[str]]
):
    """
    Assert valid state machine transition.

    Args:
        previous_state: Previous state
        current_state: Current state
        valid_transitions: Dictionary of valid transitions
    """
    valid_next_states = valid_transitions.get(previous_state, [])

    assert current_state in valid_next_states, (
        f"Invalid state transition: {previous_state} -> {current_state}. "
        f"Valid transitions from {previous_state}: {valid_next_states}"
    )
