"""Kafka streaming helpers for the analytics service."""
from __future__ import annotations

import json
import logging
import threading
from typing import Callable, Optional

from pydantic import ValidationError

try:  # pragma: no cover - optional dependency at runtime
    from kafka import KafkaConsumer, KafkaProducer
except Exception:  # pragma: no cover - kafka library may be missing at test time
    KafkaConsumer = KafkaProducer = None

from sqlalchemy.orm import Session

from .config import Settings
from .models import SensorReading
from .schemas import SensorReadingCreate

logger = logging.getLogger(__name__)


class KafkaPipeline:
    """Minimal Kafka producer/consumer integration."""

    def __init__(self, settings: Settings, session_factory: Callable[[], Session]) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._producer: Optional[KafkaProducer] = None
        self._consumer: Optional[KafkaConsumer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Initialise the consumer loop when Kafka is enabled."""

        if not self._settings.kafka_enabled:
            logger.info("Kafka integration disabled - skipping consumer startup")
            return
        if KafkaConsumer is None or KafkaProducer is None:
            logger.warning("kafka-python library unavailable - streaming disabled")
            return
        if not self._settings.kafka_broker:
            logger.warning("Kafka broker not configured - streaming disabled")
            return

        try:
            self._producer = KafkaProducer(bootstrap_servers=[self._settings.kafka_broker])
            self._consumer = KafkaConsumer(
                self._settings.kafka_topic,
                bootstrap_servers=[self._settings.kafka_broker],
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
        except Exception as exc:  # pragma: no cover - network failures hard to reproduce in tests
            logger.error("Failed to initialise Kafka components: %s", exc)
            self._producer = None
            self._consumer = None
            return

        def _consume() -> None:
            assert self._consumer is not None
            for message in self._consumer:
                try:
                    payload = json.loads(message.value.decode("utf-8"))
                    reading = SensorReadingCreate(**payload)
                except (json.JSONDecodeError, ValidationError) as exc:
                    logger.warning("Discarded malformed Kafka message: %s", exc)
                    continue

                session = self._session_factory()
                try:
                    entity = SensorReading(
                        temperature=reading.temperature,
                        pressure=reading.pressure,
                        humidity=reading.humidity,
                    )
                    session.add(entity)
                    session.commit()
                except Exception as exc:  # pragma: no cover - defensive logging
                    session.rollback()
                    logger.error("Failed to persist Kafka message: %s", exc)
                finally:
                    session.close()

        self._thread = threading.Thread(target=_consume, daemon=True)
        self._thread.start()
        logger.info("Kafka consumer thread started")

    def stop(self) -> None:
        """Shutdown Kafka resources if they were started."""

        if self._consumer is not None:
            try:
                self._consumer.close()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Error closing Kafka consumer: %s", exc)
            finally:
                self._consumer = None
        if self._producer is not None:
            try:
                self._producer.close()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Error closing Kafka producer: %s", exc)
            finally:
                self._producer = None

    def publish(self, reading: SensorReadingCreate) -> None:
        """Publish the given reading to Kafka when possible."""

        if not self._producer:
            return

        try:  # pragma: no cover - network interaction
            payload = (
                reading.model_dump()
                if hasattr(reading, "model_dump")
                else reading.dict()
            )
            self._producer.send(
                self._settings.kafka_topic,
                json.dumps(payload).encode("utf-8"),
            )
        except Exception as exc:
            logger.error("Failed to publish reading to Kafka: %s", exc)
