"""Tests for the Kafka streaming helpers."""

from __future__ import annotations

import json

from app.config import Settings
from app.schemas import SensorReadingCreate
from app.streaming import KafkaPipeline


class _DummyProducer:
    def __init__(self) -> None:
        self.sent: list[tuple[str, bytes]] = []

    def send(self, topic: str, payload: bytes) -> None:  # pragma: no cover - simple helper
        self.sent.append((topic, payload))


def test_publish_uses_model_dump() -> None:
    """Ensure publish serialises payloads in a pydantic-v1/v2 compatible way."""

    settings = Settings(kafka_enabled=True, kafka_topic="demo-topic")
    pipeline = KafkaPipeline(settings, lambda: None)
    dummy = _DummyProducer()
    pipeline._producer = dummy  # type: ignore[attr-defined]

    reading = SensorReadingCreate(temperature=21.5, pressure=101.3, humidity=55.0)

    pipeline.publish(reading)

    assert dummy.sent, "producer should receive a payload"
    topic, payload = dummy.sent[0]
    assert topic == "demo-topic"
    data = json.loads(payload.decode("utf-8"))
    assert data == reading.model_dump()
