# WhatsApp Finance Tracker - Backend API

A FastAPI-based backend for tracking personal finances through WhatsApp messages using AI-powered message parsing.

## Features
- WhatsApp integration via Twilio
- AI-powered expense message parsing
- PostgreSQL database with SQLAlchemy
- JWT authentication
- RESTful API with automatic documentation
- Docker support

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- OpenAI API key
- Twilio account (for WhatsApp)

### Installation
1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run the development server: `uvicorn app.main:app --reload`

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure
- `app/` - Main application package
- `app/api/` - API routes and endpoints
- `app/core/` - Core configuration and database setup
- `app/models/` - SQLAlchemy database models
- `app/schemas/` - Pydantic models for request/response
- `app/services/` - Business logic and external integrations
- `tests/` - Test suite

## Development Status
🚧 Work in Progress - Initial project structure setup