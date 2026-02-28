# Chargelogger

A self-hosted tool for tracking EV charging sessions across multiple cars. Chargelogger records every charge — when, where, how much energy, and what it cost — and surfaces statistics to help you understand your charging habits over time.

## Features

- **Multi-car support** – manage charging history for several vehicles independently
- **Charge Point Operator (CPO) management** – store charger networks with default per-kWh prices
- **Rich charge records** – date, odometer, kWh charged, total cost, AC/DC type, notes
- **Statistics** – monthly, yearly, and all-time breakdowns with cost and efficiency metrics
- **CSV import** – bulk-import charging history from spreadsheet exports
- **Multi-user** – each user sees only their own data; the first registered user becomes admin
- **JWT authentication** – tokens persist in browser cookies for a seamless experience

## Repository Structure

```
chargelogger/
├── backend/          # FastAPI + MongoDB API server
├── frontend/         # Streamlit web UI
├── util/             # Helper scripts (fill example data, etc.)
└── docker-compose.yml
```

See [`backend/README.md`](backend/README.md) and [`frontend/README.md`](frontend/README.md) for component-specific documentation.

## Quick Start with Docker

The easiest way to run the full stack is with Docker Compose.

```bash
docker-compose up
```

This starts three services:

| Service  | URL                        | Description          |
|----------|----------------------------|----------------------|
| API      | http://localhost:8000      | FastAPI backend      |
| Frontend | http://localhost:8501      | Streamlit UI         |
| MongoDB  | localhost:27017            | Database             |

> The API docs (Swagger UI) are available at http://localhost:8000/docs.

### First steps

1. Open http://localhost:8501 in your browser.
2. Register a new account — the first user automatically becomes admin.
3. Add a car and at least one CPO (e.g. your home wallbox).
4. Start logging charges, or import existing data via CSV.

## Environment Variables

These can be set in `docker-compose.yml` or in a `.env` file when running locally.

### Backend

| Variable                          | Default                              | Description                        |
|-----------------------------------|--------------------------------------|------------------------------------|
| `MONGODB_URL`                     | `mongodb://mongo:27017/chargelogger` | MongoDB connection string          |
| `API_SECRET_KEY`                  | *(must be set)*                      | JWT signing secret — change this!  |
| `API_ALGORITHM`                   | `HS256`                              | JWT algorithm                      |
| `API_ACCESS_TOKEN_EXPIRE_MINUTES` | `129600` (90 days)                   | Token lifetime                     |

### Frontend

| Variable                | Default                  | Description               |
|-------------------------|--------------------------|---------------------------|
| `CHARGELOGGER_BACKEND`  | `http://localhost:8000`  | URL of the backend API    |

> **Security note:** The `API_SECRET_KEY` in `docker-compose.yml` is a public example value. Always replace it with a random secret before exposing the service to a network.
