"""Application configuration utilities."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass
class Settings:
    """Runtime configuration for the analytics service."""

    app_name: str = "Real-Time Analytics Dashboard"
    database_url: str = "sqlite:///./analytics.db"
    kafka_broker: Optional[str] = None
    kafka_topic: str = "sensor-data"
    kafka_enabled: bool = False
    contamination: float = 0.1
    min_training_size: int = 10
    analytics_window: int = 200

    def __post_init__(self) -> None:
        if not 0 < self.contamination < 0.5:
            raise ValueError("contamination must be between 0 and 0.5")
        if self.min_training_size < 5:
            raise ValueError("min_training_size must be >= 5")
        if self.analytics_window <= 0:
            raise ValueError("analytics_window must be positive")

    @classmethod
    def from_env(cls) -> "Settings":
        """Create a settings instance from environment variables."""

        def _bool(name: str, default: bool) -> bool:
            value = os.getenv(name)
            if value is None:
                return default
            return value.lower() in {"1", "true", "yes", "on"}

        def _float(name: str, default: float) -> float:
            value = os.getenv(name)
            return float(value) if value is not None else default

        def _int(name: str, default: int) -> int:
            value = os.getenv(name)
            return int(value) if value is not None else default

        return cls(
            app_name=os.getenv("APP_NAME", cls.app_name),
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            kafka_broker=os.getenv("KAFKA_BROKER"),
            kafka_topic=os.getenv("KAFKA_TOPIC", cls.kafka_topic),
            kafka_enabled=_bool("ENABLE_KAFKA", cls.kafka_enabled),
            contamination=_float("ANOMALY_CONTAMINATION", cls.contamination),
            min_training_size=_int("ANOMALY_MIN_TRAINING_SIZE", cls.min_training_size),
            analytics_window=_int("ANALYTICS_WINDOW", cls.analytics_window),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""

    return Settings.from_env()
