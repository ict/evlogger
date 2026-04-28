# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

Chargelogger is a self-hosted EV charge tracker split into two top-level apps:

- **`backend/`** — FastAPI + Motor (async MongoDB) REST API. Entry point is [backend/app/main.py](backend/app/main.py); routers under `app/routes/` are mounted at `/car`, `/cpo`, `/charge`, plus `/users/*`. JWT auth (python-jose + bcrypt) with first-registered-user-becomes-admin. The API also supports long-lived API tokens (LLATs) — see `app/models/users.py` and `app/operations/users.py`.
- **`frontend/`** — React 18 SPA built with Vite. Single-file root [frontend/src/App.jsx](frontend/src/App.jsx) holds top-level state (auth, selected car, cached charges) and routes between four views in `src/views/`. All API calls go through `src/api.js`; `src/mockApi.js` powers the demo mode (login screen "Try demo" → no backend required).
- **`docker-compose.yml`** — runs `api` (internal-only), `mongo`, and `frontend` (Caddy on `127.0.0.1:8080`). Caddy reverse-proxies `/api/*` to the backend container so UI and API share one origin (see [frontend/Caddyfile](frontend/Caddyfile)).

### Backend layering

`routes/` (HTTP) → `operations/` (business logic + DB access) → `models/` (Pydantic). [backend/app/operations/crud_base.py](backend/app/operations/crud_base.py) provides a generic `CRUDBase[InCls, DbCls]` with built-in `owner_id` filtering — every list/get/update/delete passes the current user's id so users only ever see their own rows. Use this base for any new collection rather than hand-rolling Mongo queries.

A custom `DecimalCodec` is registered on every collection: pass `Decimal` in/out, BSON stores `Decimal128`. **Money and energy are integers in 1/100 units** (e.g. `2500` = 25.00 kWh, `44` = €0.44) — do not switch to floats. `price_per_kwh` on charges is computed server-side from `price_total / kwh_charged`.

Charge writes go through `_check_plausible` ([backend/app/operations/charging.py](backend/app/operations/charging.py)) which validates `car_id`/`cpo_id` ownership, denormalizes `car_name`/`cpo_name` onto the charge, and fills `price_total` from the CPO's `default_price` if omitted. Odometer values must be non-decreasing across a car's charge history.

### Frontend conventions

- Auth + base URL persist in `localStorage` under `cl_auth`. `apiClient` is rebuilt whenever auth changes; in demo mode the same shape is satisfied by `mockApi`.
- 401 from the API triggers logout (see `loadCars` in App.jsx).
- Charges are loaded once into App-level state (`limit: 500`) and shared across `ChargesView` and `YearlyTrendsView`. `DashboardView` does its own range-filtered fetches via `getCharges({ from_date, to_date })`.

## Commands

### Backend (`cd backend`)

```bash
uv sync                  # install deps (Python 3.12, uv required)
mise run run             # dev server on :8000  (or: python app/main.py)
mise run test            # full pytest suite
pytest tests/test_charges.py::test_name   # single test
```

Tests use an in-memory Mongo via `conftest.py` — no external DB needed. `mise.toml` sets `MONGODB_URL`, `API_SECRET_KEY`, etc. for local dev (the secret there is a public example).

### Frontend (`cd frontend`)

```bash
npm install
npm run dev              # Vite on :5173, proxies /api → :8000
npm run build            # outputs to dist/
```

### Full stack

```bash
docker-compose up                    # frontend at http://localhost:8080, /api/docs for Swagger
docker-compose up api mongo          # backend only (for `npm run dev`)
```

## Key environment variables

Backend requires `MONGODB_URL` and `API_SECRET_KEY`. `API_ROOT_PATH` is set to `/api` in docker-compose so FastAPI generates correct OpenAPI URLs behind the Caddy prefix strip; do not also strip it inside the app.
