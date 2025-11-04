"""Anomaly detection utilities for streaming sensor data."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List

from ..config import Settings


@dataclass
class AnomalyResult:
    """Result wrapper for anomaly detection outcomes."""

    flags: List[bool]

    @property
    def count(self) -> int:
        return sum(self.flags)

    @property
    def rate(self) -> float:
        if not self.flags:
            return 0.0
        return self.count / len(self.flags)


class AnomalyDetector:
    """Simple z-score based anomaly detector."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def detect(self, records: Iterable[dict]) -> AnomalyResult:
        readings = list(records)
        if len(readings) < self._settings.min_training_size:
            return AnomalyResult([False] * len(readings))

        temperatures = [reading.get("temperature") for reading in readings]
        pressures = [reading.get("pressure") for reading in readings]

        temp_mean = _mean(temperatures)
        pressure_mean = _mean(pressures)
        temp_std = _stddev(temperatures, temp_mean)
        pressure_std = _stddev(pressures, pressure_mean)

        flags: List[bool] = []
        threshold = max(1.0, 3.5 - self._settings.contamination * 5.0)
        for reading in readings:
            temp = reading.get("temperature")
            pressure = reading.get("pressure")
            temp_z = abs((temp - temp_mean) / temp_std) if temp_std else 0.0
            pressure_z = abs((pressure - pressure_mean) / pressure_std) if pressure_std else 0.0
            flags.append(temp_z > threshold or pressure_z > threshold)
        return AnomalyResult(flags)


def _mean(values: Iterable[float | None]) -> float:
    filtered = [value for value in values if value is not None]
    return sum(filtered) / len(filtered) if filtered else 0.0


def _stddev(values: Iterable[float | None], mean: float) -> float:
    filtered = [value for value in values if value is not None]
    if len(filtered) < 2:
        return 0.0
    variance = sum((value - mean) ** 2 for value in filtered) / (len(filtered) - 1)
    return math.sqrt(variance)
