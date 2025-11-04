from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.config import Settings
from app.main import create_app
from app.schemas import SensorReadingCreate


@pytest.fixture()
def app(tmp_path: Path) -> FastAPI:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    settings = Settings(
        database_url=database_url,
        kafka_enabled=False,
        analytics_window=50,
        min_training_size=5,
    )
    return create_app(settings)


@pytest.fixture()
def session(app: FastAPI) -> Session:
    session_factory: Callable[[], Session] = app.state.session_factory  # type: ignore[attr-defined]
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def _get_route(app: FastAPI, path: str, method: str) -> APIRoute:
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            return route
    raise AssertionError(f"Route {method} {path} not found")


def test_health_endpoint(app: FastAPI) -> None:
    route = _get_route(app, "/health", "GET")
    payload = route.endpoint()
    assert payload["status"] == "ok"


def test_ingest_and_analytics_flow(app: FastAPI, session: Session) -> None:
    post_route = _get_route(app, "/api/readings", "POST")
    get_route = _get_route(app, "/api/analytics", "GET")

    ingest = post_route.endpoint
    analytics = get_route.endpoint
    settings: Settings = app.state.settings  # type: ignore[attr-defined]

    readings = [
        {"temperature": 22.5, "pressure": 101.2, "humidity": 55.0},
        {"temperature": 22.7, "pressure": 101.4, "humidity": 54.5},
        {"temperature": 120.0, "pressure": 80.0, "humidity": 10.0},
        {"temperature": 22.4, "pressure": 101.0, "humidity": 55.2},
        {"temperature": 22.6, "pressure": 101.3, "humidity": 55.1},
    ]

    for reading in readings:
        payload = SensorReadingCreate(**reading)
        response = ingest(payload, db=session, current_settings=settings)
        assert response.temperature == pytest.approx(reading["temperature"])
        assert response.pressure == pytest.approx(reading["pressure"])

    session.commit()

    summary = analytics(window=None, db=session, current_settings=settings)
    assert summary.total_records == len(readings)
    assert summary.metrics.average_temperature == pytest.approx(
        sum(r["temperature"] for r in readings) / len(readings)
    )
    assert len(summary.recent_readings) == len(readings)


def test_invalid_window_rejected(app: FastAPI, session: Session) -> None:
    route = _get_route(app, "/api/analytics", "GET")
    analytics = route.endpoint
    settings: Settings = app.state.settings  # type: ignore[attr-defined]

    with pytest.raises(HTTPException):
        analytics(window=0, db=session, current_settings=settings)
