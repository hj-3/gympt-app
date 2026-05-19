"""Tests for data exporters."""

import csv
import json
from io import StringIO

import pytest
from exporters import (
    CSVExporter,
    JSONExporter,
    ExporterFactory,
)


@pytest.fixture
def sample_sessions():
    """Create sample workout sessions."""
    return [
        {
            "sessionId": "session-1",
            "userId": "user-123",
            "exerciseName": "Squat",
            "completedAt": "2024-05-01T10:00:00Z",
            "duration": 1800,
            "caloriesBurned": 250,
            "averageScore": 8.5,
            "status": "COMPLETED",
            "reps": 50,
            "sets": 5,
        },
        {
            "sessionId": "session-2",
            "userId": "user-123",
            "exerciseName": "Pushup",
            "completedAt": "2024-05-02T10:00:00Z",
            "duration": 1200,
            "caloriesBurned": 150,
            "averageScore": 9.0,
            "status": "COMPLETED",
            "reps": 40,
            "sets": 4,
        },
    ]


@pytest.fixture
def sample_profiles():
    """Create sample body profiles."""
    return [
        {
            "userId": "user-123",
            "recordedAt": "2024-05-01T08:00:00Z",
            "weight": 75.0,
            "height": 175,
            "bmi": 24.5,
            "bodyFat": 18.0,
            "muscleMass": 35.5,
        },
        {
            "userId": "user-123",
            "recordedAt": "2024-05-15T08:00:00Z",
            "weight": 74.5,
            "height": 175,
            "bmi": 24.3,
            "bodyFat": 17.5,
            "muscleMass": 36.0,
        },
    ]


class TestCSVExporter:
    """Test CSV exporter."""

    def test_export_with_data(self, sample_sessions, sample_profiles):
        """Test CSV export with session and profile data."""
        exporter = CSVExporter()
        result = exporter.export(sample_sessions, sample_profiles)

        assert isinstance(result, str)
        assert "WORKOUT SESSIONS" in result
        assert "BODY MEASUREMENTS" in result
        assert "Squat" in result
        assert "Pushup" in result
        assert "75.0" in result

    def test_export_sessions_only(self, sample_sessions):
        """Test CSV export with only sessions."""
        exporter = CSVExporter()
        result = exporter.export(sample_sessions, [])

        assert "WORKOUT SESSIONS" in result
        assert "session-1" in result
        assert "session-2" in result

    def test_export_profiles_only(self, sample_profiles):
        """Test CSV export with only profiles."""
        exporter = CSVExporter()
        result = exporter.export([], sample_profiles)

        assert "BODY MEASUREMENTS" in result
        assert "75.0" in result
        assert "74.5" in result

    def test_export_empty_data(self):
        """Test CSV export with no data."""
        exporter = CSVExporter()
        result = exporter.export([], [])

        # Should still have metadata
        assert "Export Date" in result
        assert "Total Sessions" in result

    def test_csv_format_validity(self, sample_sessions, sample_profiles):
        """Test that exported CSV is valid."""
        exporter = CSVExporter()
        result = exporter.export(sample_sessions, sample_profiles)

        # Should be parseable as CSV
        reader = csv.reader(StringIO(result))
        rows = list(reader)

        assert len(rows) > 0
        # Check metadata rows exist
        assert "Export Date" in rows[0]

    def test_content_type(self):
        """Test CSV content type."""
        exporter = CSVExporter()
        assert exporter.get_content_type() == "text/csv"

    def test_file_extension(self):
        """Test CSV file extension."""
        exporter = CSVExporter()
        assert exporter.get_file_extension() == "csv"


class TestJSONExporter:
    """Test JSON exporter."""

    def test_export_with_data(self, sample_sessions, sample_profiles):
        """Test JSON export with session and profile data."""
        exporter = JSONExporter()
        result = exporter.export(sample_sessions, sample_profiles)

        assert isinstance(result, str)
        data = json.loads(result)

        assert "exportMetadata" in data
        assert "summary" in data
        assert "workoutSessions" in data
        assert "bodyProfiles" in data

    def test_export_metadata(self, sample_sessions, sample_profiles):
        """Test export metadata structure."""
        exporter = JSONExporter()
        result = exporter.export(sample_sessions, sample_profiles)
        data = json.loads(result)

        metadata = data["exportMetadata"]
        assert "exportedAt" in metadata
        assert "exportVersion" in metadata
        assert metadata["format"] == "json"

    def test_summary_statistics(self, sample_sessions, sample_profiles):
        """Test summary statistics calculation."""
        exporter = JSONExporter()
        result = exporter.export(sample_sessions, sample_profiles)
        data = json.loads(result)

        summary = data["summary"]
        assert summary["totalSessions"] == 2
        assert summary["totalProfiles"] == 2
        assert "workoutStats" in summary
        assert "bodyMeasurementStats" in summary

    def test_workout_stats(self, sample_sessions, sample_profiles):
        """Test workout statistics."""
        exporter = JSONExporter()
        result = exporter.export(sample_sessions, sample_profiles)
        data = json.loads(result)

        workout_stats = data["summary"]["workoutStats"]
        assert "averageScore" in workout_stats
        assert "totalDuration" in workout_stats
        assert "totalCalories" in workout_stats
        assert "exerciseBreakdown" in workout_stats

        # Check calculations
        assert workout_stats["averageScore"] == 8.75  # (8.5 + 9.0) / 2
        assert workout_stats["totalDuration"] == 3000  # 1800 + 1200
        assert workout_stats["totalCalories"] == 400  # 250 + 150

    def test_exercise_breakdown(self, sample_sessions, sample_profiles):
        """Test exercise breakdown calculation."""
        exporter = JSONExporter()
        result = exporter.export(sample_sessions, sample_profiles)
        data = json.loads(result)

        breakdown = data["summary"]["workoutStats"]["exerciseBreakdown"]
        assert breakdown["Squat"] == 1
        assert breakdown["Pushup"] == 1

    def test_formatted_sessions(self, sample_sessions, sample_profiles):
        """Test formatted session structure."""
        exporter = JSONExporter()
        result = exporter.export(sample_sessions, sample_profiles)
        data = json.loads(result)

        sessions = data["workoutSessions"]
        assert len(sessions) == 2

        session = sessions[0]
        assert "sessionId" in session
        assert "exercise" in session
        assert "performance" in session
        assert "completedAt" in session

    def test_formatted_profiles(self, sample_sessions, sample_profiles):
        """Test formatted profile structure."""
        exporter = JSONExporter()
        result = exporter.export(sample_sessions, sample_profiles)
        data = json.loads(result)

        profiles = data["bodyProfiles"]
        assert len(profiles) == 2

        profile = profiles[0]
        assert "userId" in profile
        assert "recordedAt" in profile
        assert "measurements" in profile

    def test_export_empty_data(self):
        """Test JSON export with no data."""
        exporter = JSONExporter()
        result = exporter.export([], [])
        data = json.loads(result)

        assert data["summary"]["totalSessions"] == 0
        assert data["summary"]["totalProfiles"] == 0
        assert len(data["workoutSessions"]) == 0
        assert len(data["bodyProfiles"]) == 0

    def test_content_type(self):
        """Test JSON content type."""
        exporter = JSONExporter()
        assert exporter.get_content_type() == "application/json"

    def test_file_extension(self):
        """Test JSON file extension."""
        exporter = JSONExporter()
        assert exporter.get_file_extension() == "json"


class TestExporterFactory:
    """Test exporter factory."""

    def test_get_csv_exporter(self):
        """Test getting CSV exporter."""
        exporter = ExporterFactory.get_exporter("csv")
        assert isinstance(exporter, CSVExporter)

        exporter = ExporterFactory.get_exporter("CSV")
        assert isinstance(exporter, CSVExporter)

    def test_get_json_exporter(self):
        """Test getting JSON exporter."""
        exporter = ExporterFactory.get_exporter("json")
        assert isinstance(exporter, JSONExporter)

        exporter = ExporterFactory.get_exporter("JSON")
        assert isinstance(exporter, JSONExporter)

    def test_unsupported_format(self):
        """Test unsupported format raises error."""
        with pytest.raises(ValueError) as exc_info:
            ExporterFactory.get_exporter("xml")

        assert "Unsupported export format" in str(exc_info.value)

    def test_factory_export_method(self, sample_sessions, sample_profiles):
        """Test factory export method."""
        csv_result = ExporterFactory.export("csv", sample_sessions, sample_profiles)
        assert "WORKOUT SESSIONS" in csv_result

        json_result = ExporterFactory.export("json", sample_sessions, sample_profiles)
        data = json.loads(json_result)
        assert "workoutSessions" in data

    def test_get_content_type(self):
        """Test getting content type via factory."""
        assert ExporterFactory.get_content_type("csv") == "text/csv"
        assert ExporterFactory.get_content_type("json") == "application/json"

    def test_get_file_extension(self):
        """Test getting file extension via factory."""
        assert ExporterFactory.get_file_extension("csv") == "csv"
        assert ExporterFactory.get_file_extension("json") == "json"


class TestExportConsistency:
    """Test consistency across exporters."""

    def test_both_formats_contain_all_data(self, sample_sessions, sample_profiles):
        """Test that both formats contain all data."""
        csv_result = ExporterFactory.export("csv", sample_sessions, sample_profiles)
        json_result = ExporterFactory.export("json", sample_sessions, sample_profiles)

        # CSV should contain all session IDs
        for session in sample_sessions:
            assert session["sessionId"] in csv_result

        # JSON should contain all session IDs
        json_data = json.loads(json_result)
        session_ids = [s["sessionId"] for s in json_data["workoutSessions"]]
        for session in sample_sessions:
            assert session["sessionId"] in session_ids

    def test_both_formats_handle_empty_data(self):
        """Test both formats handle empty data gracefully."""
        csv_result = ExporterFactory.export("csv", [], [])
        json_result = ExporterFactory.export("json", [], [])

        assert len(csv_result) > 0  # Should have headers
        json_data = json.loads(json_result)
        assert json_data["summary"]["totalSessions"] == 0


class TestEdgeCases:
    """Test edge cases."""

    def test_sessions_with_missing_fields(self):
        """Test handling sessions with missing optional fields."""
        sessions = [
            {
                "sessionId": "session-1",
                "userId": "user-123",
                "exerciseName": "Squat",
                # Missing some optional fields
            }
        ]

        csv_exporter = CSVExporter()
        csv_result = csv_exporter.export(sessions, [])
        assert "session-1" in csv_result

        json_exporter = JSONExporter()
        json_result = json_exporter.export(sessions, [])
        data = json.loads(json_result)
        assert len(data["workoutSessions"]) == 1

    def test_large_dataset(self):
        """Test handling large dataset."""
        sessions = [
            {
                "sessionId": f"session-{i}",
                "userId": "user-123",
                "exerciseName": "Squat",
                "averageScore": 8.0,
                "status": "COMPLETED",
            }
            for i in range(1000)
        ]

        exporter = JSONExporter()
        result = exporter.export(sessions, [])
        data = json.loads(result)

        assert data["summary"]["totalSessions"] == 1000
        assert len(data["workoutSessions"]) == 1000
