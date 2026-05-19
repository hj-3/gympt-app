import pytest
from app.pose_estimator.mock_estimator import MockPoseEstimator
from app.rules.squat_rule import SquatRule


@pytest.mark.asyncio
async def test_squat_good_form():
    """Test squat analysis with good form."""
    estimator = MockPoseEstimator()
    rule = SquatRule(estimator)
    
    # Mock pose data with good form
    pose_data = {
        "keypoints": {
            "left_knee": {"x": 0.4, "y": 0.75, "confidence": 0.9},
            "right_knee": {"x": 0.6, "y": 0.75, "confidence": 0.9},
            "left_ankle": {"x": 0.38, "y": 0.9, "confidence": 0.9},
            "right_ankle": {"x": 0.62, "y": 0.9, "confidence": 0.9},
            "left_hip": {"x": 0.42, "y": 0.8, "confidence": 0.9},
            "left_shoulder": {"x": 0.4, "y": 0.35, "confidence": 0.9}
        }
    }
    
    result = await rule.analyze(pose_data)
    
    assert result["exercise"] == "squat"
    assert result["score"] >= 8.0
    assert result["is_good_form"] is True


@pytest.mark.asyncio
async def test_squat_knee_valgus():
    """Test squat with knee valgus issue."""
    estimator = MockPoseEstimator()
    rule = SquatRule(estimator)
    
    # Mock pose data with knees caving in
    pose_data = {
        "keypoints": {
            "left_knee": {"x": 0.45, "y": 0.75, "confidence": 0.9},
            "right_knee": {"x": 0.55, "y": 0.75, "confidence": 0.9},
            "left_ankle": {"x": 0.38, "y": 0.9, "confidence": 0.9},
            "right_ankle": {"x": 0.62, "y": 0.9, "confidence": 0.9},
            "left_hip": {"x": 0.42, "y": 0.8, "confidence": 0.9},
            "left_shoulder": {"x": 0.4, "y": 0.35, "confidence": 0.9}
        }
    }
    
    result = await rule.analyze(pose_data)
    
    assert result["score"] < 10.0
    assert len(result["issues"]) > 0
    
    # Check for knee valgus issue
    issue_types = [issue["type"] for issue in result["issues"]]
    assert "knee_valgus" in issue_types


@pytest.mark.asyncio
async def test_squat_insufficient_depth():
    """Test squat with insufficient depth."""
    estimator = MockPoseEstimator()
    rule = SquatRule(estimator)
    
    pose_data = {
        "keypoints": {
            "left_knee": {"x": 0.4, "y": 0.75, "confidence": 0.9},
            "right_knee": {"x": 0.6, "y": 0.75, "confidence": 0.9},
            "left_ankle": {"x": 0.38, "y": 0.9, "confidence": 0.9},
            "right_ankle": {"x": 0.62, "y": 0.9, "confidence": 0.9},
            "left_hip": {"x": 0.42, "y": 0.6, "confidence": 0.9},  # Hip too high
            "left_shoulder": {"x": 0.4, "y": 0.35, "confidence": 0.9}
        }
    }
    
    result = await rule.analyze(pose_data)
    
    issue_types = [issue["type"] for issue in result["issues"]]
    assert "insufficient_depth" in issue_types
