# Real-Time Analytics Dashboard

A portfolio-ready project showcasing a modern FastAPI backend that ingests streaming sensor
telemetry, persists it to a relational database, and surfaces anomaly-aware analytics.

## ✨ Features

- **FastAPI microservice** with typed request/response models and health checks
- **SQLAlchemy ORM** persistence with pluggable database URL (SQLite for local dev, Postgres in production)
- **Statistical anomaly detection** using streaming z-score calculations to flag suspicious readings
- **Optional Kafka integration** for real-time ingestion pipelines
- **Comprehensive automated tests** using `pytest` to validate ingestion and analytics flows

## 🗂 Project structure

```
backend/
  app/
    config.py          # Dataclass configuration with environment variable support
    core/database.py   # SQLAlchemy engine/session factory helpers
    main.py            # FastAPI application factory and routes
    models.py          # SQLAlchemy ORM models
    schemas.py         # Pydantic schemas for validation and serialization
    services/
      anomaly.py       # Z-score based anomaly detection utilities
      analytics.py     # Aggregation helpers for metrics and anomaly summaries
    streaming.py       # Kafka producer/consumer integration
  requirements.txt     # Backend dependencies (API + testing stack)
  tests/
    test_api.py        # API-level tests covering ingestion and analytics
```

## 🚀 Getting started

### 1. Create a virtual environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables (optional)

Copy `.env.example` to `.env` and set values for:

- `DATABASE_URL` – defaults to local SQLite (`sqlite:///./analytics.db`)
- `ENABLE_KAFKA`, `KAFKA_BROKER`, `KAFKA_TOPIC` – enable Kafka integration when you have a broker available
- `ANOMALY_CONTAMINATION`, `ANOMALY_MIN_TRAINING_SIZE`, `ANALYTICS_WINDOW` – tune anomaly sensitivity and aggregation window

### 4. Run the API locally

```bash
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive Swagger documentation.

## 🧪 Running the tests

```bash
cd backend
pytest
```

The tests spin up the FastAPI app with an ephemeral SQLite database to validate ingestion,
analytics summaries, and error handling.

## 🧱 Docker & infrastructure

A starter `docker-compose.yml` is included for local infrastructure components:

- `backend` – the FastAPI service served via Uvicorn
- `kafka` / `zookeeper` – Apache Kafka stack for streaming ingestion
- `postgres` – PostgreSQL for production-ready persistence

Start them with:

```bash
docker-compose up
```

Then point the API at Postgres and Kafka via environment variables.

## 📚 Portfolio talking points

- Designed a modular FastAPI service with clear separation between configuration,
  persistence, analytics, and streaming concerns
- Implemented automated anomaly detection on streaming telemetry using lightweight
  statistics (no heavy ML dependencies required)
- Added pytest coverage to ensure regression-safe refactors and document expected behaviour
- Produced detailed project documentation suitable for GitHub and resume bullet points
