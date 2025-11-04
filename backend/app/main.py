"""FastAPI entrypoint for the real-time analytics dashboard."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .core.database import Base, create_session_factory
from .models import SensorReading
from .schemas import AnalyticsResponse, SensorReadingCreate, SensorReadingRead
from .services.analytics import summarize_readings
from .streaming import KafkaPipeline

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    settings = settings or get_settings()
    engine, session_factory = create_session_factory(settings.database_url)
    Base.metadata.create_all(bind=engine)

    pipeline = KafkaPipeline(settings, session_factory)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # pragma: no cover - lightweight bootstrap
        pipeline.start()
        try:
            yield
        finally:
            pipeline.stop()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = session_factory

    def get_db() -> Callable[[], Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def get_current_settings() -> Settings:
        return settings

    @app.get("/health", tags=["health"])
    def health() -> dict:
        """Simple health-check endpoint."""

        return {"status": "ok", "app": settings.app_name}

    @app.post("/api/readings", response_model=SensorReadingRead, status_code=status.HTTP_201_CREATED, tags=["readings"])
    def ingest_reading(
        payload: SensorReadingCreate,
        db: Session = Depends(get_db),
        current_settings: Settings = Depends(get_current_settings),
    ) -> SensorReadingRead:
        """Persist an incoming sensor reading and publish to Kafka when enabled."""

        entity = SensorReading(
            temperature=payload.temperature,
            pressure=payload.pressure,
            humidity=payload.humidity,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)

        if current_settings.kafka_enabled:
            pipeline.publish(payload)

        return SensorReadingRead.model_validate(entity, from_attributes=True)

    @app.get("/api/analytics", response_model=AnalyticsResponse, tags=["analytics"])
    def analytics(
        window: int | None = None,
        db: Session = Depends(get_db),
        current_settings: Settings = Depends(get_current_settings),
    ) -> AnalyticsResponse:
        """Return a summary of recent readings along with anomaly detection results."""

        if window is not None and window <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="window must be positive")

        return summarize_readings(db, current_settings, limit=window)

    return app


app = create_app()
