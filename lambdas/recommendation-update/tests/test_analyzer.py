"""Tests for performance analyzer."""

import pytest
from analyzer import PerformanceAnalyzer, PerformanceMetrics, RecommendationDecision


@pytest.fixture
def analyzer():
    """Create analyzer instance."""
    return PerformanceAnalyzer()


@pytest.fixture
def excellent_sessions():
    """Create sessions with excellent performance."""
    return [
        {
            "sessionId": f"session-{i}",
            "averageScore": 9.0,
            "status": "COMPLETED",
            "exerciseName": "Squat",
        }
        for i in range(5)
    ]


@pytest.fixture
def poor_sessions():
    """Create sessions with poor performance."""
    return [
        {
            "sessionId": f"session-{i}",
            "averageScore": 5.0,
            "status": "COMPLETED",
            "exerciseName": "Squat",
        }
        for i in range(5)
    ]


@pytest.fixture
def declining_sessions():
    """Create sessions with declining performance."""
    return [
        {"sessionId": f"session-{i}", "averageScore": 9.0 - i * 0.5, "status": "COMPLETED"}
        for i in range(5)
    ]


class TestPerformanceAnalyzer:
    """Test performance analyzer."""

    def test_insufficient_sessions(self, analyzer):
        """Test with insufficient session data."""
        sessions = [
            {"sessionId": "session-1", "averageScore": 8.0, "status": "COMPLETED"}
        ]

        decision = analyzer.analyze(sessions)

        assert decision.action == "MAINTAIN"
        assert decision.confidence == 0.5
        assert "Insufficient data" in decision.reason

    def test_excellent_performance_increase(self, analyzer, excellent_sessions):
        """Test recommendation for excellent performance."""
        decision = analyzer.analyze(excellent_sessions)

        assert decision.action == "INCREASE"
        assert decision.confidence >= 0.8
        assert "Excellent performance" in decision.reason
        assert len(decision.recommendations) > 0
        assert any("increase" in r.lower() for r in decision.recommendations)

    def test_poor_performance_decrease(self, analyzer, poor_sessions):
        """Test recommendation for poor performance."""
        decision = analyzer.analyze(poor_sessions)

        assert decision.action == "DECREASE"
        assert decision.confidence >= 0.8
        assert "Low form score" in decision.reason or "Low completion rate" in decision.reason
        assert len(decision.recommendations) > 0
        assert any("reduce" in r.lower() or "focus on form" in r.lower() for r in decision.recommendations)

    def test_low_completion_rate_decrease(self, analyzer):
        """Test recommendation for low completion rate."""
        sessions = [
            {"sessionId": f"session-{i}", "averageScore": 8.0, "status": "INCOMPLETE" if i % 2 == 0 else "COMPLETED"}
            for i in range(5)
        ]

        decision = analyzer.analyze(sessions)

        assert decision.action == "DECREASE"
        assert "Low completion rate" in decision.reason

    def test_good_performance_maintain(self, analyzer):
        """Test recommendation for good performance."""
        sessions = [
            {"sessionId": f"session-{i}", "averageScore": 7.5, "status": "COMPLETED"}
            for i in range(5)
        ]

        decision = analyzer.analyze(sessions)

        assert decision.action == "MAINTAIN"
        assert decision.confidence >= 0.7

    def test_improving_trend(self, analyzer):
        """Test detection of improving trend."""
        sessions = [
            {"sessionId": f"session-{i}", "averageScore": 7.0 + i * 0.3, "status": "COMPLETED"}
            for i in range(6)
        ]

        decision = analyzer.analyze(sessions)

        # Should maintain but with positive feedback
        assert decision.action == "MAINTAIN"
        assert any("progress" in r.lower() or "improving" in r.lower() for r in decision.recommendations)

    def test_declining_trend(self, analyzer, declining_sessions):
        """Test detection of declining trend."""
        decision = analyzer.analyze(declining_sessions)

        # Either decrease or maintain with warning
        assert decision.action in ["DECREASE", "MAINTAIN"]
        if decision.action == "MAINTAIN":
            assert any("monitor" in r.lower() or "review" in r.lower() for r in decision.recommendations)


class TestCalculateMetrics:
    """Test metrics calculation."""

    def test_calculate_average_score(self, analyzer):
        """Test average score calculation."""
        sessions = [
            {"sessionId": "1", "averageScore": 8.0, "status": "COMPLETED"},
            {"sessionId": "2", "averageScore": 9.0, "status": "COMPLETED"},
            {"sessionId": "3", "averageScore": 7.0, "status": "COMPLETED"},
        ]

        metrics = analyzer._calculate_metrics(sessions)

        assert metrics.average_score == 8.0
        assert metrics.completion_rate == 1.0
        assert metrics.total_sessions == 3

    def test_calculate_completion_rate(self, analyzer):
        """Test completion rate calculation."""
        sessions = [
            {"sessionId": "1", "averageScore": 8.0, "status": "COMPLETED"},
            {"sessionId": "2", "averageScore": 8.0, "status": "INCOMPLETE"},
            {"sessionId": "3", "averageScore": 8.0, "status": "COMPLETED"},
            {"sessionId": "4", "averageScore": 8.0, "status": "INCOMPLETE"},
        ]

        metrics = analyzer._calculate_metrics(sessions)

        assert metrics.completion_rate == 0.5

    def test_calculate_trend_improving(self, analyzer):
        """Test trend calculation for improving performance."""
        scores = [6.0, 6.5, 7.0, 7.5, 8.0, 8.5]
        trend = analyzer._calculate_trend(scores)

        assert trend == "IMPROVING"

    def test_calculate_trend_declining(self, analyzer):
        """Test trend calculation for declining performance."""
        scores = [8.5, 8.0, 7.5, 7.0, 6.5, 6.0]
        trend = analyzer._calculate_trend(scores)

        assert trend == "DECLINING"

    def test_calculate_trend_stable(self, analyzer):
        """Test trend calculation for stable performance."""
        scores = [7.5, 7.6, 7.4, 7.5, 7.6, 7.4]
        trend = analyzer._calculate_trend(scores)

        assert trend == "STABLE"


class TestDetailedAnalysis:
    """Test detailed analysis output."""

    def test_detailed_analysis_structure(self, analyzer):
        """Test detailed analysis return structure."""
        sessions = [
            {
                "sessionId": f"session-{i}",
                "averageScore": 8.0,
                "status": "COMPLETED",
                "exerciseName": "Squat" if i % 2 == 0 else "Pushup",
            }
            for i in range(6)
        ]

        analysis = analyzer.get_detailed_analysis(sessions)

        assert "overallMetrics" in analysis
        assert "recommendation" in analysis
        assert "exerciseBreakdown" in analysis

        # Check overall metrics
        assert "averageScore" in analysis["overallMetrics"]
        assert "completionRate" in analysis["overallMetrics"]
        assert "totalSessions" in analysis["overallMetrics"]
        assert "trend" in analysis["overallMetrics"]

        # Check recommendation
        assert "action" in analysis["recommendation"]
        assert "confidence" in analysis["recommendation"]
        assert "reason" in analysis["recommendation"]
        assert "recommendations" in analysis["recommendation"]

        # Check exercise breakdown
        assert "Squat" in analysis["exerciseBreakdown"]
        assert "Pushup" in analysis["exerciseBreakdown"]

    def test_detailed_analysis_empty_sessions(self, analyzer):
        """Test detailed analysis with empty sessions."""
        analysis = analyzer.get_detailed_analysis([])

        assert "error" in analysis
        assert analysis["error"] == "No sessions to analyze"

    def test_exercise_breakdown_calculation(self, analyzer):
        """Test exercise-specific breakdown."""
        sessions = [
            {"sessionId": "1", "averageScore": 9.0, "status": "COMPLETED", "exerciseName": "Squat"},
            {"sessionId": "2", "averageScore": 8.0, "status": "COMPLETED", "exerciseName": "Squat"},
            {"sessionId": "3", "averageScore": 7.0, "status": "COMPLETED", "exerciseName": "Pushup"},
        ]

        analysis = analyzer.get_detailed_analysis(sessions)

        squat_data = analysis["exerciseBreakdown"]["Squat"]
        assert squat_data["count"] == 2
        assert squat_data["averageScore"] == 8.5

        pushup_data = analysis["exerciseBreakdown"]["Pushup"]
        assert pushup_data["count"] == 1
        assert pushup_data["averageScore"] == 7.0


class TestEdgeCases:
    """Test edge cases."""

    def test_sessions_without_scores(self, analyzer):
        """Test handling sessions without average scores."""
        sessions = [
            {"sessionId": "1", "status": "COMPLETED"},
            {"sessionId": "2", "status": "COMPLETED"},
        ]

        metrics = analyzer._calculate_metrics(sessions)

        assert metrics.average_score == 0.0
        assert metrics.completion_rate == 1.0

    def test_mixed_statuses(self, analyzer):
        """Test handling various session statuses."""
        sessions = [
            {"sessionId": "1", "averageScore": 8.0, "status": "COMPLETED"},
            {"sessionId": "2", "averageScore": 7.0, "status": "INCOMPLETE"},
            {"sessionId": "3", "averageScore": 9.0, "status": "COMPLETED"},
            {"sessionId": "4", "averageScore": 6.0, "status": "CANCELLED"},
        ]

        metrics = analyzer._calculate_metrics(sessions)

        # Only COMPLETED sessions should count for completion rate
        assert metrics.completion_rate == 0.5
        # All sessions should be included in score average
        assert metrics.average_score == 7.5
