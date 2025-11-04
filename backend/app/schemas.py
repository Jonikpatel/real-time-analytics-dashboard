"""Pydantic schemas for request and response payloads."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class SensorReadingCreate(BaseModel):
    """Payload used to ingest a new sensor reading."""

    temperature: float = Field(..., description="Measured temperature in degrees Celsius")
    pressure: float = Field(..., description="Measured pressure in kPa")
    humidity: Optional[float] = Field(None, description="Relative humidity percentage")


class SensorReadingRead(SensorReadingCreate):
    """Representation of a stored sensor reading."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SensorMetrics(BaseModel):
    """Aggregate statistics computed from recent readings."""

    average_temperature: Optional[float] = None
    average_pressure: Optional[float] = None
    average_humidity: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_pressure: Optional[float] = None
    max_pressure: Optional[float] = None


class AnalyticsResponse(BaseModel):
    """Summary analytics returned by the dashboard API."""

    total_records: int
    anomalies: int
    anomaly_rate: float
    metrics: SensorMetrics
    recent_readings: List[SensorReadingRead]
