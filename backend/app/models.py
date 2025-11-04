"""Database models for the analytics domain."""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, func

from .core.database import Base


class SensorReading(Base):
    """Persisted sensor reading streamed into the platform."""

    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float, nullable=False)
    pressure = Column(Float, nullable=False)
    humidity = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:  # pragma: no cover - repr utility
        return (
            "SensorReading(id={id}, temperature={temperature}, pressure={pressure}, "
            "humidity={humidity}, created_at={created_at})"
        ).format(
            id=self.id,
            temperature=self.temperature,
            pressure=self.pressure,
            humidity=self.humidity,
            created_at=self.created_at,
        )
