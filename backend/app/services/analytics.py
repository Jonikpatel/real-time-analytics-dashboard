"""Analytics helpers for summarising sensor readings."""
from __future__ import annotations

from typing import List, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import SensorReading
from ..schemas import AnalyticsResponse, SensorMetrics, SensorReadingRead
from .anomaly import AnomalyDetector


def _to_schema(readings: Sequence[SensorReading]) -> List[SensorReadingRead]:
    return [SensorReadingRead.model_validate(reading, from_attributes=True) for reading in readings]


def _mean(values: List[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _min(values: List[float]) -> float | None:
    return min(values) if values else None


def _max(values: List[float]) -> float | None:
    return max(values) if values else None


def fetch_recent_readings(db: Session, limit: int) -> List[SensorReading]:
    """Return the most recent readings ordered from oldest to newest."""

    stmt = select(SensorReading).order_by(SensorReading.created_at.desc()).limit(limit)
    results = list(db.execute(stmt).scalars())
    results.reverse()
    return results


def summarize_readings(db: Session, settings: Settings, limit: int | None = None) -> AnalyticsResponse:
    """Build an :class:`AnalyticsResponse` using the persisted sensor readings."""

    window = limit or settings.analytics_window
    readings = fetch_recent_readings(db, window)

    temperatures = [reading.temperature for reading in readings if reading.temperature is not None]
    pressures = [reading.pressure for reading in readings if reading.pressure is not None]
    humidities = [reading.humidity for reading in readings if reading.humidity is not None]

    metrics = SensorMetrics(
        average_temperature=_mean(temperatures),
        average_pressure=_mean(pressures),
        average_humidity=_mean(humidities),
        min_temperature=_min(temperatures),
        max_temperature=_max(temperatures),
        min_pressure=_min(pressures),
        max_pressure=_max(pressures),
    )

    records = [
        {
            "temperature": reading.temperature,
            "pressure": reading.pressure,
            "humidity": reading.humidity,
        }
        for reading in readings
    ]

    detector = AnomalyDetector(settings)
    anomaly_result = detector.detect(records)

    return AnalyticsResponse(
        total_records=len(readings),
        anomalies=anomaly_result.count,
        anomaly_rate=anomaly_result.rate,
        metrics=metrics,
        recent_readings=_to_schema(readings),
    )
