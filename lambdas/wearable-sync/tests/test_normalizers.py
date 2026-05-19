"""Tests for wearable data normalizers."""

import pytest
from normalizers import (
    AppleWatchNormalizer,
    FitbitNormalizer,
    GarminNormalizer,
    NormalizerFactory,
)


class TestAppleWatchNormalizer:
    """Test Apple Watch normalizer."""

    def test_normalize_complete_data(self):
        """Test normalization with all fields."""
        normalizer = AppleWatchNormalizer()
        raw_data = {
            "heartRate": 75,
            "steps": 1000,
            "calories": 50,
            "activeMinutes": 10,
            "distance": 0.8,
            "sleepMinutes": 480,
        }

        result = normalizer.normalize(raw_data)

        assert result["heartRate"] == 75
        assert result["steps"] == 1000
        assert result["calories"] == 50
        assert result["activeMinutes"] == 10
        assert result["distance"] == 0.8
        assert result["sleepMinutes"] == 480

    def test_normalize_partial_data(self):
        """Test normalization with missing optional fields."""
        normalizer = AppleWatchNormalizer()
        raw_data = {
            "heartRate": 80,
            "steps": 500,
            "calories": 25,
        }

        result = normalizer.normalize(raw_data)

        assert result["heartRate"] == 80
        assert result["steps"] == 500
        assert result["calories"] == 25
        assert "distance" not in result
        assert "sleepMinutes" not in result


class TestFitbitNormalizer:
    """Test Fitbit normalizer."""

    def test_normalize_complete_data(self):
        """Test normalization with all fields."""
        normalizer = FitbitNormalizer()
        raw_data = {
            "heart_rate": 72,
            "steps": 1200,
            "calories_burned": 60,
            "active_minutes": 15,
            "distance_km": 1.0,
            "sleep_duration_minutes": 420,
            "resting_heart_rate": 65,
            "floors_climbed": 3,
        }

        result = normalizer.normalize(raw_data)

        assert result["heartRate"] == 72
        assert result["steps"] == 1200
        assert result["calories"] == 60
        assert result["activeMinutes"] == 15
        assert result["distance"] == 1.0
        assert result["sleepMinutes"] == 420
        assert result["restingHeartRate"] == 65
        assert result["floorsClimbed"] == 3

    def test_normalize_minimal_data(self):
        """Test normalization with minimal required fields."""
        normalizer = FitbitNormalizer()
        raw_data = {
            "steps": 800,
            "calories_burned": 40,
        }

        result = normalizer.normalize(raw_data)

        assert result["steps"] == 800
        assert result["calories"] == 40
        assert len(result) == 2


class TestGarminNormalizer:
    """Test Garmin normalizer."""

    def test_normalize_complete_data(self):
        """Test normalization with all fields."""
        normalizer = GarminNormalizer()
        raw_data = {
            "hr": 78,
            "step_count": 1500,
            "kcal": 70,
            "active_time_minutes": 20,
            "distance_meters": 1200,
            "sleep_time_seconds": 28800,
            "vo2_max": 45,
            "stress_level": 30,
        }

        result = normalizer.normalize(raw_data)

        assert result["heartRate"] == 78
        assert result["steps"] == 1500
        assert result["calories"] == 70
        assert result["activeMinutes"] == 20
        assert result["distance"] == 1.2  # Converted from meters to km
        assert result["sleepMinutes"] == 480  # Converted from seconds to minutes
        assert result["vo2Max"] == 45
        assert result["stressLevel"] == 30

    def test_normalize_unit_conversions(self):
        """Test unit conversions for distance and sleep."""
        normalizer = GarminNormalizer()
        raw_data = {
            "distance_meters": 5000,  # 5 km
            "sleep_time_seconds": 25200,  # 420 minutes (7 hours)
        }

        result = normalizer.normalize(raw_data)

        assert result["distance"] == 5.0
        assert result["sleepMinutes"] == 420


class TestNormalizerFactory:
    """Test normalizer factory."""

    def test_get_apple_watch_normalizer(self):
        """Test getting Apple Watch normalizer."""
        normalizer = NormalizerFactory.get_normalizer("apple_watch")
        assert isinstance(normalizer, AppleWatchNormalizer)

        normalizer = NormalizerFactory.get_normalizer("APPLE_WATCH")
        assert isinstance(normalizer, AppleWatchNormalizer)

    def test_get_fitbit_normalizer(self):
        """Test getting Fitbit normalizer."""
        normalizer = NormalizerFactory.get_normalizer("fitbit")
        assert isinstance(normalizer, FitbitNormalizer)

        normalizer = NormalizerFactory.get_normalizer("FITBIT")
        assert isinstance(normalizer, FitbitNormalizer)

    def test_get_garmin_normalizer(self):
        """Test getting Garmin normalizer."""
        normalizer = NormalizerFactory.get_normalizer("garmin")
        assert isinstance(normalizer, GarminNormalizer)

        normalizer = NormalizerFactory.get_normalizer("GARMIN")
        assert isinstance(normalizer, GarminNormalizer)

    def test_unknown_device_type(self):
        """Test unknown device type defaults to Apple Watch."""
        normalizer = NormalizerFactory.get_normalizer("unknown_device")
        assert isinstance(normalizer, AppleWatchNormalizer)

    def test_normalize_factory_method(self):
        """Test factory normalize method."""
        raw_data = {
            "heart_rate": 70,
            "steps": 1000,
            "calories_burned": 50,
        }

        result = NormalizerFactory.normalize("fitbit", raw_data)

        assert result["heartRate"] == 70
        assert result["steps"] == 1000
        assert result["calories"] == 50


class TestCrossPlatformConsistency:
    """Test that all normalizers produce consistent output format."""

    def test_all_normalizers_produce_same_keys(self):
        """Test that common metrics have consistent key names."""
        apple_data = {
            "heartRate": 75,
            "steps": 1000,
            "calories": 50,
        }

        fitbit_data = {
            "heart_rate": 75,
            "steps": 1000,
            "calories_burned": 50,
        }

        garmin_data = {
            "hr": 75,
            "step_count": 1000,
            "kcal": 50,
        }

        apple_result = NormalizerFactory.normalize("apple_watch", apple_data)
        fitbit_result = NormalizerFactory.normalize("fitbit", fitbit_data)
        garmin_result = NormalizerFactory.normalize("garmin", garmin_data)

        # All should have same keys
        common_keys = {"heartRate", "steps", "calories"}
        assert common_keys.issubset(set(apple_result.keys()))
        assert common_keys.issubset(set(fitbit_result.keys()))
        assert common_keys.issubset(set(garmin_result.keys()))

        # All should have same values
        assert apple_result["heartRate"] == fitbit_result["heartRate"] == garmin_result["heartRate"]
        assert apple_result["steps"] == fitbit_result["steps"] == garmin_result["steps"]
        assert apple_result["calories"] == fitbit_result["calories"] == garmin_result["calories"]
