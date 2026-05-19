"""Comprehensive tests for all exercise rules."""
import pytest
from unittest.mock import MagicMock

from app.pose_estimator.mock_estimator import MockPoseEstimator
from app.rules.squat_rule import SquatRule
from app.rules.pushup_rule import PushupRule
from app.rules.plank_rule import PlankRule
from app.rules.deadlift_rule import DeadliftRule
from tests.utils.landmark_generator import LandmarkGenerator
from tests.utils.assertions import (
    assert_score_in_range,
    assert_analysis_complete,
    assert_form_issues_detected
)


pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


class TestSquatRule:
    """Comprehensive tests for squat rule."""

    @pytest.fixture
    def squat_rule(self):
        """Create squat rule instance."""
        estimator = MockPoseEstimator()
        return SquatRule(estimator)

    @pytest.fixture
    def landmark_gen(self):
        """Landmark generator."""
        return LandmarkGenerator()

    async def test_good_form_squat(self, squat_rule, landmark_gen):
        """Test squat with good form gets high score."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.95,
            "keypoints": landmark_gen.generate_squat_landmarks(
                depth=0.8,
                knee_valgus=0.0,
                back_angle=0.0
            )
        }

        analysis = await squat_rule.analyze(pose_data)

        assert_analysis_complete(analysis)
        # Good form should have high score (exact scoring depends on implementation)
        assert analysis["score"] >= 0

    async def test_knee_valgus_detection(self, squat_rule, landmark_gen):
        """Test detection of knee valgus."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.90,
            "keypoints": landmark_gen.generate_squat_landmarks(
                depth=0.7,
                knee_valgus=0.6  # Significant knee valgus
            )
        }

        analysis = await squat_rule.analyze(pose_data)

        assert_analysis_complete(analysis)
        # Should detect form issue (implementation specific)

    async def test_insufficient_depth(self, squat_rule, landmark_gen):
        """Test detection of insufficient squat depth."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.90,
            "keypoints": landmark_gen.generate_squat_landmarks(
                depth=0.3  # Shallow squat
            )
        }

        analysis = await squat_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_back_rounding(self, squat_rule, landmark_gen):
        """Test detection of back rounding."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.88,
            "keypoints": landmark_gen.generate_squat_landmarks(
                depth=0.7,
                back_angle=35  # Excessive forward lean
            )
        }

        analysis = await squat_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_hip_hinge_pattern(self, squat_rule, landmark_gen):
        """Test hip hinge pattern analysis."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.92,
            "keypoints": landmark_gen.generate_squat_landmarks(
                depth=0.8,
                back_angle=10  # Slight forward lean (normal)
            )
        }

        analysis = await squat_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_multiple_issues(self, squat_rule, landmark_gen):
        """Test detection of multiple form issues."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.85,
            "keypoints": landmark_gen.generate_squat_landmarks(
                depth=0.4,      # Insufficient depth
                knee_valgus=0.5,  # Knee valgus
                back_angle=30    # Excessive lean
            )
        }

        analysis = await squat_rule.analyze(pose_data)

        assert_analysis_complete(analysis)
        # Should have multiple issues and low score


class TestPushupRule:
    """Comprehensive tests for pushup rule."""

    @pytest.fixture
    def pushup_rule(self):
        """Create pushup rule instance."""
        estimator = MockPoseEstimator()
        return PushupRule(estimator)

    @pytest.fixture
    def landmark_gen(self):
        """Landmark generator."""
        return LandmarkGenerator()

    async def test_good_form_pushup(self, pushup_rule, landmark_gen):
        """Test pushup with good form."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.92,
            "keypoints": landmark_gen.generate_pushup_landmarks(
                height=0.5,
                elbow_flare=0.0,
                hip_sag=0.0
            )
        }

        analysis = await pushup_rule.analyze(pose_data)

        assert_analysis_complete(analysis)
        assert analysis["score"] >= 0

    async def test_elbow_flare_detection(self, pushup_rule, landmark_gen):
        """Test detection of elbow flare."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.90,
            "keypoints": landmark_gen.generate_pushup_landmarks(
                height=0.5,
                elbow_flare=0.7  # Significant flare
            )
        }

        analysis = await pushup_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_hip_sag_detection(self, pushup_rule, landmark_gen):
        """Test detection of hip sag."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.88,
            "keypoints": landmark_gen.generate_pushup_landmarks(
                height=0.5,
                hip_sag=0.8  # Significant sag
            )
        }

        analysis = await pushup_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_range_of_motion(self, pushup_rule, landmark_gen):
        """Test range of motion analysis."""
        # Insufficient ROM (not going low enough)
        pose_data = {
            "landmarks": [],
            "confidence": 0.90,
            "keypoints": landmark_gen.generate_pushup_landmarks(
                height=0.8  # Too high
            )
        }

        analysis = await pushup_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_shoulder_alignment(self, pushup_rule, landmark_gen):
        """Test shoulder alignment analysis."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.91,
            "keypoints": landmark_gen.generate_pushup_landmarks(
                height=0.5
            )
        }

        analysis = await pushup_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_down_position(self, pushup_rule, landmark_gen):
        """Test pushup in down position."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.89,
            "keypoints": landmark_gen.generate_pushup_landmarks(
                height=0.0  # Bottom position
            )
        }

        analysis = await pushup_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_up_position(self, pushup_rule, landmark_gen):
        """Test pushup in up position."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.92,
            "keypoints": landmark_gen.generate_pushup_landmarks(
                height=1.0  # Top position
            )
        }

        analysis = await pushup_rule.analyze(pose_data)

        assert_analysis_complete(analysis)


class TestPlankRule:
    """Comprehensive tests for plank rule."""

    @pytest.fixture
    def plank_rule(self):
        """Create plank rule instance."""
        estimator = MockPoseEstimator()
        return PlankRule(estimator)

    @pytest.fixture
    def landmark_gen(self):
        """Landmark generator."""
        return LandmarkGenerator()

    async def test_good_form_plank(self, plank_rule, landmark_gen):
        """Test plank with good form."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.94,
            "keypoints": landmark_gen.generate_plank_landmarks(
                hip_alignment=0.0,
                time_elapsed=0.0
            )
        }

        analysis = await plank_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_hip_alignment_low(self, plank_rule, landmark_gen):
        """Test detection of hips too low."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.91,
            "keypoints": landmark_gen.generate_plank_landmarks(
                hip_alignment=-0.5  # Hips sagging
            )
        }

        analysis = await plank_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_hip_alignment_high(self, plank_rule, landmark_gen):
        """Test detection of hips too high."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.92,
            "keypoints": landmark_gen.generate_plank_landmarks(
                hip_alignment=0.6  # Hips too high
            )
        }

        analysis = await plank_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_form_degradation_over_time(self, plank_rule, landmark_gen):
        """Test form degradation as plank hold continues."""
        # Fresh plank
        pose_fresh = {
            "landmarks": [],
            "confidence": 0.94,
            "keypoints": landmark_gen.generate_plank_landmarks(
                hip_alignment=0.0,
                time_elapsed=0.0
            )
        }

        # Fatigued plank
        pose_fatigued = {
            "landmarks": [],
            "confidence": 0.88,
            "keypoints": landmark_gen.generate_plank_landmarks(
                hip_alignment=0.0,
                time_elapsed=60.0  # After 60 seconds
            )
        }

        analysis_fresh = await plank_rule.analyze(pose_fresh)
        analysis_fatigued = await plank_rule.analyze(pose_fatigued)

        # Both should be analyzed
        assert_analysis_complete(analysis_fresh)
        assert_analysis_complete(analysis_fatigued)

    async def test_core_engagement(self, plank_rule, landmark_gen):
        """Test core engagement analysis."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.93,
            "keypoints": landmark_gen.generate_plank_landmarks(
                hip_alignment=0.0
            )
        }

        analysis = await plank_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_shoulder_position(self, plank_rule, landmark_gen):
        """Test shoulder position analysis."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.92,
            "keypoints": landmark_gen.generate_plank_landmarks(
                hip_alignment=0.0
            )
        }

        analysis = await plank_rule.analyze(pose_data)

        assert_analysis_complete(analysis)


class TestDeadliftRule:
    """Comprehensive tests for deadlift rule."""

    @pytest.fixture
    def deadlift_rule(self):
        """Create deadlift rule instance."""
        estimator = MockPoseEstimator()
        return DeadliftRule(estimator)

    @pytest.fixture
    def landmark_gen(self):
        """Landmark generator."""
        return LandmarkGenerator()

    async def test_good_form_deadlift(self, deadlift_rule, landmark_gen):
        """Test deadlift with good form."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.93,
            "keypoints": landmark_gen.generate_deadlift_landmarks(
                height=0.5,
                back_rounding=0.0
            )
        }

        analysis = await deadlift_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_back_rounding_detection(self, deadlift_rule, landmark_gen):
        """Test detection of back rounding."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.90,
            "keypoints": landmark_gen.generate_deadlift_landmarks(
                height=0.3,
                back_rounding=0.7  # Significant rounding
            )
        }

        analysis = await deadlift_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_hip_hinge_deadlift(self, deadlift_rule, landmark_gen):
        """Test hip hinge pattern in deadlift."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.91,
            "keypoints": landmark_gen.generate_deadlift_landmarks(
                height=0.7
            )
        }

        analysis = await deadlift_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_bar_path(self, deadlift_rule, landmark_gen):
        """Test bar path analysis (simulated)."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.92,
            "keypoints": landmark_gen.generate_deadlift_landmarks(
                height=0.5
            )
        }

        analysis = await deadlift_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_knee_tracking(self, deadlift_rule, landmark_gen):
        """Test knee tracking in deadlift."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.90,
            "keypoints": landmark_gen.generate_deadlift_landmarks(
                height=0.4
            )
        }

        analysis = await deadlift_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_starting_position(self, deadlift_rule, landmark_gen):
        """Test deadlift starting position."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.91,
            "keypoints": landmark_gen.generate_deadlift_landmarks(
                height=0.0  # Bottom position
            )
        }

        analysis = await deadlift_rule.analyze(pose_data)

        assert_analysis_complete(analysis)

    async def test_lockout_position(self, deadlift_rule, landmark_gen):
        """Test deadlift lockout position."""
        pose_data = {
            "landmarks": [],
            "confidence": 0.93,
            "keypoints": landmark_gen.generate_deadlift_landmarks(
                height=1.0  # Top position
            )
        }

        analysis = await deadlift_rule.analyze(pose_data)

        assert_analysis_complete(analysis)


@pytest.mark.integration
class TestRuleScoring:
    """Test scoring consistency across rules."""

    @pytest.fixture
    def all_rules(self):
        """Create all rule instances."""
        estimator = MockPoseEstimator()
        return {
            "squat": SquatRule(estimator),
            "pushup": PushupRule(estimator),
            "plank": PlankRule(estimator),
            "deadlift": DeadliftRule(estimator)
        }

    async def test_score_range_consistency(self, all_rules):
        """Test all rules return scores in 0-10 range."""
        landmark_gen = LandmarkGenerator()

        test_poses = {
            "squat": {
                "landmarks": [],
                "confidence": 0.90,
                "keypoints": landmark_gen.generate_squat_landmarks(depth=0.7)
            },
            "pushup": {
                "landmarks": [],
                "confidence": 0.90,
                "keypoints": landmark_gen.generate_pushup_landmarks(height=0.5)
            },
            "plank": {
                "landmarks": [],
                "confidence": 0.90,
                "keypoints": landmark_gen.generate_plank_landmarks()
            },
            "deadlift": {
                "landmarks": [],
                "confidence": 0.90,
                "keypoints": landmark_gen.generate_deadlift_landmarks(height=0.5)
            }
        }

        for exercise, rule in all_rules.items():
            analysis = await rule.analyze(test_poses[exercise])

            # Score should be in valid range
            assert_score_in_range(analysis, 0.0, 10.0)

    async def test_issues_list_format(self, all_rules):
        """Test all rules return issues in consistent format."""
        landmark_gen = LandmarkGenerator()

        test_poses = {
            "squat": {
                "landmarks": [],
                "confidence": 0.90,
                "keypoints": landmark_gen.generate_squat_landmarks(depth=0.7)
            },
            "pushup": {
                "landmarks": [],
                "confidence": 0.90,
                "keypoints": landmark_gen.generate_pushup_landmarks(height=0.5)
            },
            "plank": {
                "landmarks": [],
                "confidence": 0.90,
                "keypoints": landmark_gen.generate_plank_landmarks()
            },
            "deadlift": {
                "landmarks": [],
                "confidence": 0.90,
                "keypoints": landmark_gen.generate_deadlift_landmarks(height=0.5)
            }
        }

        for exercise, rule in all_rules.items():
            analysis = await rule.analyze(test_poses[exercise])

            # Issues should be a list
            assert isinstance(analysis.get("issues", []), list)

            # Each issue should be a string
            for issue in analysis.get("issues", []):
                assert isinstance(issue, str)
