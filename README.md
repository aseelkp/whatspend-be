# WhatsApp Finance Tracker - Backend API

A FastAPI backend for tracking personal finances from WhatsApp messages using AI-powered parsing (Google Gemini).

## Features

- WhatsApp integration via Twilio
- AI-powered expense parsing (Google Gemini)
- PostgreSQL with SQLAlchemy
- JWT authentication
- REST API with OpenAPI docs
- Docker support

## Prerequisites

- **Python 3.12+**
- **uv** – [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **PostgreSQL 15+** (local or Docker)
- **Google Gemini API key**
- **Twilio account** (optional; app runs without it but WhatsApp features need it)

## Run from scratch

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd whatspend-BE
```

### 2. Install dependencies (uv)

```bash
uv sync
```

Uses `pyproject.toml` and `uv.lock`; no `requirements.txt` needed.

### 3. Environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at least:


| Variable                 | Description                                                                          |
| ------------------------ | ------------------------------------------------------------------------------------ |
| `DATABASE_URL`           | PostgreSQL URL, e.g. `postgresql://postgres:password@localhost:5432/finance_tracker` |
| `JWT_SECRET_KEY`         | Long random secret for JWT (use a strong value in production)                        |
| `GEMINI_API_KEY`         | Google Gemini API key (required for message parsing)                                 |
| `TWILIO_ACCOUNT_SID`     | Twilio SID (optional)                                                                |
| `TWILIO_AUTH_TOKEN`      | Twilio token (optional)                                                              |
| `TWILIO_WHATSAPP_NUMBER` | e.g. `whatsapp:+14155238886` (optional)                                              |
| `DASHBOARD_URL`          | Frontend URL for magic links, e.g. `http://localhost:5173` (optional)                |


### 4. Database

Start PostgreSQL (e.g. with Docker):

```bash
docker-compose up -d postgres
```

Create the database if needed (e.g. `createdb finance_tracker`), then run migrations:

```bash
alembic upgrade head
```

Seed default categories (groceries, transportation, etc.):

```bash
python -m app.core.seed_data
```

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

- API: **[http://localhost:8000](http://localhost:8000)**
- Health: **[http://localhost:8000/health](http://localhost:8000/health)**
- Swagger: **[http://localhost:8000/docs](http://localhost:8000/docs)**
- ReDoc: **[http://localhost:8000/redoc](http://localhost:8000/redoc)**

## Run with Docker

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Build and run the app (ensure .env exists and DATABASE_URL is correct)
docker build -t whatspend-be .
docker run -p 8000:8000 --env-file .env whatspend-be
```

## API Documentation

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Project structure

- `app/` – Main application package
- `app/api/` – API routes and endpoints 
- `app/core/` – Config and database setup
- `app/models/` – SQLAlchemy models
- `app/schemas/` – Pydantic request/response models
- `app/services/` – Business logic and integrations
- `tests/` – Test suite

## Development

- Install (including dev deps): `uv sync`
- Add a dependency: `uv add <package>`
- Regenerate lockfile: `uv lock`

## Development status

Work in progress – initial project structure and core features.