# EVLogger

A self-hosted tool for tracking EV charging sessions and the full cost of owning your cars. EVLogger records every charge — when, where, how much energy, and what it cost — along with other car expenses, and surfaces statistics to help you understand your charging habits and total cost of ownership over time.

## Features

- **Multi-car support** – manage charging history for several vehicles independently
- **Charge Point Operator (CPO) management** – store charger networks with default per-kWh prices
- **Rich charge records** – date, odometer, kWh charged, total cost, AC/DC type, notes
- **Expenses** – insurance, tax, tires, tolls & parking, cleaning, maintenance, accessories, subscriptions and more
- **Total cost of ownership** – purchase and sale price per car, running and all-in cost per 100 km; retire sold cars
- **Statistics** – monthly, yearly, and all-time breakdowns with cost and efficiency metrics
- **CSV import** – bulk-import charging history from spreadsheet exports
- **Multi-user** – each user sees only their own data; the first registered user becomes admin
- **JWT authentication** – tokens persist in browser cookies for a seamless experience

## Repository Structure

```
evlogger/
├── backend/          # FastAPI + MongoDB API server
├── frontend/         # React (Vite) SPA, served by Caddy + reverse-proxies /api
└── docker-compose.yml
```

See [`backend/README.md`](backend/README.md) and [`frontend/README.md`](frontend/README.md) for component-specific documentation.

## Quick Start with Docker

The easiest way to run the full stack is with Docker Compose.

```bash
echo "API_SECRET_KEY=$(openssl rand -hex 32)" > .env
docker compose up
```

`API_SECRET_KEY` signs login tokens. Compose refuses to start without it, and the backend
rejects known example keys and keys shorter than 32 characters.

This starts three services:

| Service          | URL                          | Description                          |
|------------------|------------------------------|--------------------------------------|
| Frontend + API   | http://localhost:8080        | React SPA (Caddy proxies `/api/*`)   |
| MongoDB          | localhost:27017              | Database                             |

> The API docs (Swagger UI) are available at http://localhost:8080/api/docs.
> The API container is internal-only — reach it through the Caddy proxy.

### First steps

1. Open http://localhost:8080 in your browser.
2. Register a new account — the first user automatically becomes admin.
3. Add a car and at least one CPO (e.g. your home wallbox).
4. Start logging charges, or import existing data via CSV.

## Environment Variables

These can be set in `docker-compose.yml` or in a `.env` file when running locally.

### Backend

| Variable                          | Default                              | Description                        |
|-----------------------------------|--------------------------------------|------------------------------------|
| `MONGODB_URL`                     | `mongodb://mongo:27017/chargelogger` | MongoDB connection string          |
| `API_SECRET_KEY`                  | *(must be set)*                      | JWT signing secret, ≥ 32 chars     |
| `API_ALGORITHM`                   | `HS256`                              | JWT algorithm                      |
| `API_ACCESS_TOKEN_EXPIRE_MINUTES` | `129600` (90 days)                   | Token lifetime                     |

### Frontend

The frontend is a static bundle. It calls the API at the relative path `/api`,
which Caddy reverse-proxies to the backend container.

| Variable             | Default | Description                                                                 |
|----------------------|---------|-----------------------------------------------------------------------------|
| `VITE_DEMO_ENABLED`  | `false` | Set to `true` to show the "Try demo" button on the login screen. Configure in `frontend/.env.local` for local dev or pass at build time for production. |


## License

[MIT](LICENSE)
