"""Data exporters for different file formats."""

import csv
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from io import StringIO
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Base class for data exporters."""

    @abstractmethod
    def export(
        self, sessions: List[Dict[str, Any]], profiles: List[Dict[str, Any]]
    ) -> str:
        """Export data to string format."""
        pass

    @abstractmethod
    def get_content_type(self) -> str:
        """Get MIME content type."""
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension."""
        pass


class CSVExporter(BaseExporter):
    """Export data to CSV format."""

    def export(
        self, sessions: List[Dict[str, Any]], profiles: List[Dict[str, Any]]
    ) -> str:
        """Export workout data to CSV format."""
        output = StringIO()
        writer = csv.writer(output)

        # Export metadata
        writer.writerow(["Export Date", datetime.utcnow().isoformat()])
        writer.writerow(["Total Sessions", len(sessions)])
        writer.writerow(["Total Profiles", len(profiles)])
        writer.writerow([])

        # Workout sessions section
        if sessions:
            writer.writerow(["=== WORKOUT SESSIONS ==="])
            writer.writerow([
                "Session ID",
                "User ID",
                "Exercise Name",
                "Completed At",
                "Duration (seconds)",
                "Calories Burned",
                "Average Score",
                "Status",
                "Reps",
                "Sets",
            ])

            for session in sessions:
                writer.writerow([
                    session.get("sessionId", ""),
                    session.get("userId", ""),
                    session.get("exerciseName", ""),
                    session.get("completedAt", ""),
                    session.get("duration", ""),
                    session.get("caloriesBurned", ""),
                    session.get("averageScore", ""),
                    session.get("status", "COMPLETED"),
                    session.get("reps", ""),
                    session.get("sets", ""),
                ])

            writer.writerow([])

        # Body profiles section
        if profiles:
            writer.writerow(["=== BODY MEASUREMENTS ==="])
            writer.writerow([
                "User ID",
                "Recorded At",
                "Weight (kg)",
                "Height (cm)",
                "BMI",
                "Body Fat (%)",
                "Muscle Mass (kg)",
            ])

            for profile in profiles:
                writer.writerow([
                    profile.get("userId", ""),
                    profile.get("recordedAt", ""),
                    profile.get("weight", ""),
                    profile.get("height", ""),
                    profile.get("bmi", ""),
                    profile.get("bodyFat", ""),
                    profile.get("muscleMass", ""),
                ])

        csv_content = output.getvalue()
        output.close()

        logger.info(
            f"CSV export completed: {len(sessions)} sessions, {len(profiles)} profiles"
        )
        return csv_content

    def get_content_type(self) -> str:
        """Get MIME content type."""
        return "text/csv"

    def get_file_extension(self) -> str:
        """Get file extension."""
        return "csv"


class JSONExporter(BaseExporter):
    """Export data to JSON format."""

    def export(
        self, sessions: List[Dict[str, Any]], profiles: List[Dict[str, Any]]
    ) -> str:
        """Export workout data to JSON format."""
        # Calculate summary statistics
        summary = self._calculate_summary(sessions, profiles)

        data = {
            "exportMetadata": {
                "exportedAt": datetime.utcnow().isoformat(),
                "exportVersion": "1.0",
                "format": "json",
            },
            "summary": summary,
            "workoutSessions": self._format_sessions(sessions),
            "bodyProfiles": self._format_profiles(profiles),
        }

        json_content = json.dumps(data, indent=2, default=str)

        logger.info(
            f"JSON export completed: {len(sessions)} sessions, {len(profiles)} profiles"
        )
        return json_content

    def _format_sessions(self, sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format workout sessions for JSON export."""
        formatted = []
        for session in sessions:
            formatted_session = {
                "sessionId": session.get("sessionId"),
                "userId": session.get("userId"),
                "exercise": {
                    "name": session.get("exerciseName"),
                    "reps": session.get("reps"),
                    "sets": session.get("sets"),
                },
                "performance": {
                    "averageScore": session.get("averageScore"),
                    "duration": session.get("duration"),
                    "caloriesBurned": session.get("caloriesBurned"),
                },
                "completedAt": session.get("completedAt"),
                "status": session.get("status", "COMPLETED"),
            }
            formatted.append(formatted_session)

        return formatted

    def _format_profiles(self, profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format body profiles for JSON export."""
        formatted = []
        for profile in profiles:
            formatted_profile = {
                "userId": profile.get("userId"),
                "recordedAt": profile.get("recordedAt"),
                "measurements": {
                    "weight": profile.get("weight"),
                    "height": profile.get("height"),
                    "bmi": profile.get("bmi"),
                    "bodyFat": profile.get("bodyFat"),
                    "muscleMass": profile.get("muscleMass"),
                },
            }
            formatted.append(formatted_profile)

        return formatted

    def _calculate_summary(
        self, sessions: List[Dict[str, Any]], profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate summary statistics."""
        summary = {
            "totalSessions": len(sessions),
            "totalProfiles": len(profiles),
        }

        if sessions:
            # Calculate workout statistics
            scores = [
                s.get("averageScore", 0)
                for s in sessions
                if s.get("averageScore") is not None
            ]
            durations = [
                s.get("duration", 0) for s in sessions if s.get("duration") is not None
            ]
            calories = [
                s.get("caloriesBurned", 0)
                for s in sessions
                if s.get("caloriesBurned") is not None
            ]

            summary["workoutStats"] = {
                "averageScore": round(sum(scores) / len(scores), 2) if scores else 0,
                "totalDuration": sum(durations),
                "totalCalories": sum(calories),
                "exerciseBreakdown": self._get_exercise_breakdown(sessions),
            }

        if profiles:
            # Calculate body measurement trends
            summary["bodyMeasurementStats"] = {
                "recordingCount": len(profiles),
                "latestWeight": profiles[-1].get("weight") if profiles else None,
                "latestBMI": profiles[-1].get("bmi") if profiles else None,
            }

        return summary

    def _get_exercise_breakdown(self, sessions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of sessions by exercise type."""
        breakdown = {}
        for session in sessions:
            exercise = session.get("exerciseName", "Unknown")
            breakdown[exercise] = breakdown.get(exercise, 0) + 1

        return breakdown

    def get_content_type(self) -> str:
        """Get MIME content type."""
        return "application/json"

    def get_file_extension(self) -> str:
        """Get file extension."""
        return "json"


class ExporterFactory:
    """Factory for creating exporters."""

    _exporters = {
        "csv": CSVExporter,
        "json": JSONExporter,
    }

    @classmethod
    def get_exporter(cls, format: str) -> BaseExporter:
        """Get exporter for format."""
        exporter_class = cls._exporters.get(format.lower())

        if not exporter_class:
            raise ValueError(f"Unsupported export format: {format}")

        return exporter_class()

    @classmethod
    def export(
        cls,
        format: str,
        sessions: List[Dict[str, Any]],
        profiles: List[Dict[str, Any]],
    ) -> str:
        """Export data using specified format."""
        exporter = cls.get_exporter(format)
        return exporter.export(sessions, profiles)

    @classmethod
    def get_content_type(cls, format: str) -> str:
        """Get content type for format."""
        exporter = cls.get_exporter(format)
        return exporter.get_content_type()

    @classmethod
    def get_file_extension(cls, format: str) -> str:
        """Get file extension for format."""
        exporter = cls.get_exporter(format)
        return exporter.get_file_extension()
