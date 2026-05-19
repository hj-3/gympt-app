"""Device-specific normalizers for wearable data."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BaseNormalizer(ABC):
    """Base class for device normalizers."""

    @abstractmethod
    def normalize(self, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw metrics to common format."""
        pass

    def _safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely get value from dictionary."""
        return data.get(key, default)


class AppleWatchNormalizer(BaseNormalizer):
    """Normalizer for Apple Watch data (HealthKit format)."""

    def normalize(self, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Apple Watch/HealthKit data.

        Expected format:
        {
            "heartRate": 75,
            "steps": 1000,
            "calories": 50,
            "activeMinutes": 10,
            "distance": 0.8,
            "sleepMinutes": 480
        }
        """
        normalized = {
            "heartRate": self._safe_get(raw_metrics, "heartRate"),
            "steps": self._safe_get(raw_metrics, "steps", 0),
            "calories": self._safe_get(raw_metrics, "calories", 0),
            "activeMinutes": self._safe_get(raw_metrics, "activeMinutes", 0),
            "distance": self._safe_get(raw_metrics, "distance"),
            "sleepMinutes": self._safe_get(raw_metrics, "sleepMinutes"),
        }

        # Remove None values
        normalized = {k: v for k, v in normalized.items() if v is not None}

        logger.info(f"Normalized Apple Watch metrics: {len(normalized)} fields")
        return normalized


class FitbitNormalizer(BaseNormalizer):
    """Normalizer for Fitbit data."""

    def normalize(self, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Fitbit data.

        Expected format:
        {
            "heart_rate": 75,
            "steps": 1000,
            "calories_burned": 50,
            "active_minutes": 10,
            "distance_km": 0.8,
            "sleep_duration_minutes": 480,
            "resting_heart_rate": 60,
            "floors_climbed": 5
        }
        """
        normalized = {
            "heartRate": self._safe_get(raw_metrics, "heart_rate"),
            "steps": self._safe_get(raw_metrics, "steps", 0),
            "calories": self._safe_get(raw_metrics, "calories_burned", 0),
            "activeMinutes": self._safe_get(raw_metrics, "active_minutes", 0),
            "distance": self._safe_get(raw_metrics, "distance_km"),
            "sleepMinutes": self._safe_get(raw_metrics, "sleep_duration_minutes"),
            "restingHeartRate": self._safe_get(raw_metrics, "resting_heart_rate"),
            "floorsClimbed": self._safe_get(raw_metrics, "floors_climbed"),
        }

        # Remove None values
        normalized = {k: v for k, v in normalized.items() if v is not None}

        logger.info(f"Normalized Fitbit metrics: {len(normalized)} fields")
        return normalized


class GarminNormalizer(BaseNormalizer):
    """Normalizer for Garmin data."""

    def normalize(self, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Garmin data.

        Expected format:
        {
            "hr": 75,
            "step_count": 1000,
            "kcal": 50,
            "active_time_minutes": 10,
            "distance_meters": 800,
            "sleep_time_seconds": 28800,
            "vo2_max": 45,
            "stress_level": 30
        }
        """
        # Convert sleep from seconds to minutes
        sleep_seconds = self._safe_get(raw_metrics, "sleep_time_seconds")
        sleep_minutes = sleep_seconds // 60 if sleep_seconds else None

        # Convert distance from meters to km
        distance_meters = self._safe_get(raw_metrics, "distance_meters")
        distance_km = distance_meters / 1000 if distance_meters else None

        normalized = {
            "heartRate": self._safe_get(raw_metrics, "hr"),
            "steps": self._safe_get(raw_metrics, "step_count", 0),
            "calories": self._safe_get(raw_metrics, "kcal", 0),
            "activeMinutes": self._safe_get(raw_metrics, "active_time_minutes", 0),
            "distance": distance_km,
            "sleepMinutes": sleep_minutes,
            "vo2Max": self._safe_get(raw_metrics, "vo2_max"),
            "stressLevel": self._safe_get(raw_metrics, "stress_level"),
        }

        # Remove None values
        normalized = {k: v for k, v in normalized.items() if v is not None}

        logger.info(f"Normalized Garmin metrics: {len(normalized)} fields")
        return normalized


class NormalizerFactory:
    """Factory for creating device normalizers."""

    _normalizers = {
        "apple_watch": AppleWatchNormalizer,
        "APPLE_WATCH": AppleWatchNormalizer,
        "fitbit": FitbitNormalizer,
        "FITBIT": FitbitNormalizer,
        "garmin": GarminNormalizer,
        "GARMIN": GarminNormalizer,
    }

    @classmethod
    def get_normalizer(cls, device_type: str) -> BaseNormalizer:
        """Get normalizer for device type."""
        normalizer_class = cls._normalizers.get(device_type)

        if not normalizer_class:
            logger.warning(f"Unknown device type: {device_type}, using base normalization")
            # Return a generic normalizer that passes through data
            return AppleWatchNormalizer()

        return normalizer_class()

    @classmethod
    def normalize(cls, device_type: str, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize metrics for device type."""
        normalizer = cls.get_normalizer(device_type)
        return normalizer.normalize(raw_metrics)
