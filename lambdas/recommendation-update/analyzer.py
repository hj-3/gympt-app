"""Performance analyzer for workout recommendation adjustments."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Workout performance metrics."""

    average_score: float
    completion_rate: float
    total_sessions: int
    trend: str = "STABLE"  # IMPROVING, STABLE, DECLINING


@dataclass
class RecommendationDecision:
    """Recommendation adjustment decision."""

    action: str  # INCREASE, MAINTAIN, DECREASE
    confidence: float  # 0.0 to 1.0
    reason: str
    recommendations: List[str]


class PerformanceAnalyzer:
    """Analyze workout performance and recommend intensity adjustments."""

    # Thresholds for decision-making
    EXCELLENT_SCORE_THRESHOLD = 8.5
    GOOD_SCORE_THRESHOLD = 7.0
    POOR_SCORE_THRESHOLD = 6.0

    HIGH_COMPLETION_THRESHOLD = 0.9
    LOW_COMPLETION_THRESHOLD = 0.5

    MIN_SESSIONS_FOR_ADJUSTMENT = 3

    def __init__(self):
        """Initialize analyzer."""
        self.logger = logging.getLogger(__name__)

    def analyze(
        self, sessions: List[Dict[str, Any]], min_sessions: int = MIN_SESSIONS_FOR_ADJUSTMENT
    ) -> RecommendationDecision:
        """
        Analyze workout sessions and recommend intensity adjustment.

        Args:
            sessions: List of recent workout sessions
            min_sessions: Minimum sessions required for analysis

        Returns:
            RecommendationDecision with action and reasoning
        """
        if len(sessions) < min_sessions:
            return RecommendationDecision(
                action="MAINTAIN",
                confidence=0.5,
                reason=f"Insufficient data ({len(sessions)}/{min_sessions} sessions)",
                recommendations=["Complete more workouts for personalized recommendations"],
            )

        # Calculate metrics
        metrics = self._calculate_metrics(sessions)
        self.logger.info(
            f"Performance metrics: score={metrics.average_score:.2f}, "
            f"completion={metrics.completion_rate:.2f}, trend={metrics.trend}"
        )

        # Make decision
        return self._make_decision(metrics)

    def _calculate_metrics(self, sessions: List[Dict[str, Any]]) -> PerformanceMetrics:
        """Calculate performance metrics from sessions."""
        # Average score
        scores = [s.get("averageScore", 0) for s in sessions if "averageScore" in s]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Completion rate
        completed = sum(1 for s in sessions if s.get("status") == "COMPLETED")
        completion_rate = completed / len(sessions) if sessions else 0.0

        # Calculate trend (compare first half vs second half)
        trend = self._calculate_trend(scores)

        return PerformanceMetrics(
            average_score=avg_score,
            completion_rate=completion_rate,
            total_sessions=len(sessions),
            trend=trend,
        )

    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate performance trend."""
        if len(scores) < 4:
            return "STABLE"

        mid_point = len(scores) // 2
        first_half_avg = sum(scores[:mid_point]) / mid_point
        second_half_avg = sum(scores[mid_point:]) / (len(scores) - mid_point)

        improvement = second_half_avg - first_half_avg

        if improvement >= 0.5:
            return "IMPROVING"
        elif improvement <= -0.5:
            return "DECLINING"
        else:
            return "STABLE"

    def _make_decision(self, metrics: PerformanceMetrics) -> RecommendationDecision:
        """Make recommendation decision based on metrics."""
        score = metrics.average_score
        completion = metrics.completion_rate
        trend = metrics.trend

        # Decision: INCREASE intensity
        if (
            score >= self.EXCELLENT_SCORE_THRESHOLD
            and completion >= self.HIGH_COMPLETION_THRESHOLD
        ):
            return RecommendationDecision(
                action="INCREASE",
                confidence=0.9,
                reason=f"Excellent performance: {score:.1f}/10 avg score, {completion*100:.0f}% completion",
                recommendations=[
                    "Increase weight by 5-10% for strength exercises",
                    "Add 1-2 more reps per set",
                    "Reduce rest time between sets by 10-15 seconds",
                    "Consider progressive overload techniques",
                ],
            )

        # Decision: DECREASE intensity
        if score < self.POOR_SCORE_THRESHOLD or completion < self.LOW_COMPLETION_THRESHOLD:
            reasons = []
            if score < self.POOR_SCORE_THRESHOLD:
                reasons.append(f"Low form score: {score:.1f}/10")
            if completion < self.LOW_COMPLETION_THRESHOLD:
                reasons.append(f"Low completion rate: {completion*100:.0f}%")

            return RecommendationDecision(
                action="DECREASE",
                confidence=0.85,
                reason=", ".join(reasons),
                recommendations=[
                    "Reduce weight by 10-15%",
                    "Focus on proper form over intensity",
                    "Increase rest time between sets",
                    "Consider active recovery days",
                    "Review exercise technique with coach",
                ],
            )

        # Decision: MAINTAIN with nuanced recommendations
        if trend == "IMPROVING":
            recommendations = [
                "Maintain current intensity - you're making good progress",
                "Continue focusing on form consistency",
                "Track progress for potential increase next week",
            ]
            confidence = 0.8
        elif trend == "DECLINING":
            recommendations = [
                "Maintain current intensity but monitor closely",
                "Review form and technique",
                "Ensure adequate rest and recovery",
                "Consider reducing volume if fatigue persists",
            ]
            confidence = 0.7
        else:
            recommendations = [
                "Maintain current intensity",
                "Continue focusing on form",
                "Good consistent performance",
            ]
            confidence = 0.75

        return RecommendationDecision(
            action="MAINTAIN",
            confidence=confidence,
            reason=f"Good performance: {score:.1f}/10 avg score, trend: {trend}",
            recommendations=recommendations,
        )

    def get_detailed_analysis(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get detailed performance analysis."""
        if not sessions:
            return {"error": "No sessions to analyze"}

        metrics = self._calculate_metrics(sessions)
        decision = self._make_decision(metrics)

        # Exercise-specific analysis
        exercise_breakdown = {}
        for session in sessions:
            exercise = session.get("exerciseName", "Unknown")
            if exercise not in exercise_breakdown:
                exercise_breakdown[exercise] = {"count": 0, "scores": []}

            exercise_breakdown[exercise]["count"] += 1
            if "averageScore" in session:
                exercise_breakdown[exercise]["scores"].append(session["averageScore"])

        # Calculate per-exercise averages
        for exercise, data in exercise_breakdown.items():
            scores = data["scores"]
            data["averageScore"] = sum(scores) / len(scores) if scores else 0.0

        return {
            "overallMetrics": {
                "averageScore": round(metrics.average_score, 2),
                "completionRate": round(metrics.completion_rate, 2),
                "totalSessions": metrics.total_sessions,
                "trend": metrics.trend,
            },
            "recommendation": {
                "action": decision.action,
                "confidence": decision.confidence,
                "reason": decision.reason,
                "recommendations": decision.recommendations,
            },
            "exerciseBreakdown": {
                exercise: {
                    "count": data["count"],
                    "averageScore": round(data["averageScore"], 2),
                }
                for exercise, data in exercise_breakdown.items()
            },
        }
