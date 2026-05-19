import pytest
from app.pose_estimator.mock_estimator import MockPoseEstimator
from app.rules.pushup_rule import PushupRule


@pytest.mark.asyncio
async def test_pushup_good_form():
    """Test push-up with good form."""
    estimator = MockPoseEstimator()
    rule = PushupRule(estimator)
    
    pose_data = {
        "keypoints": {
            "left_shoulder": {"x": 0.4, "y": 0.35, "confidence": 0.9},
            "left_elbow": {"x": 0.35, "y": 0.5, "confidence": 0.9},
            "left_wrist": {"x": 0.3, "y": 0.65, "confidence": 0.9},
            "left_hip": {"x": 0.42, "y": 0.6, "confidence": 0.9},
            "left_ankle": {"x": 0.38, "y": 0.9, "confidence": 0.9}
        }
    }
    
    result = await rule.analyze(pose_data)
    
    assert result["exercise"] == "pushup"
    assert result["score"] >= 0.0


@pytest.mark.asyncio
async def test_pushup_hip_sag():
    """Test push-up with hip sag."""
    estimator = MockPoseEstimator()
    rule = PushupRule(estimator)
    
    pose_data = {
        "keypoints": {
            "left_shoulder": {"x": 0.4, "y": 0.35, "confidence": 0.9},
            "left_elbow": {"x": 0.35, "y": 0.5, "confidence": 0.9},
            "left_wrist": {"x": 0.3, "y": 0.65, "confidence": 0.9},
            "left_hip": {"x": 0.42, "y": 0.75, "confidence": 0.9},  # Hip sagging
            "left_ankle": {"x": 0.38, "y": 0.9, "confidence": 0.9}
        }
    }
    
    result = await rule.analyze(pose_data)
    
    issue_types = [issue["type"] for issue in result["issues"]]
    assert "hip_sag" in issue_types
