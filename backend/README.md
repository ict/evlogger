# EVLogger — Backend

Async REST API built with **FastAPI** and **MongoDB**. Handles user authentication, car and CPO management, charge and expense storage, and CSV import.

## Features

- JWT-based authentication with bcrypt password hashing
- First registered user automatically becomes admin
- Full CRUD for cars, Charge Point Operators (CPOs), and charge records
- Odometer consistency validation (prevents decreasing values over time)
- Automatic CPO default-price fallback when no price is supplied
- Flexible time-range filtering on charge queries (`timespan`, `from_date`, `to_date`)
- CSV bulk import with auto-encoding detection and auto-CPO creation
- Decimal-safe monetary and energy math (all values stored as integer 1/100 units)
- Per-user data isolation — users can only access their own records

## Tech Stack

| Component       | Library / Version             |
|-----------------|-------------------------------|
| Framework       | FastAPI >= 0.100              |
| ASGI server     | Uvicorn >= 0.23               |
| Production WSGI | Gunicorn >= 20.1              |
| Database        | MongoDB via Motor >= 3.2 (async) |
| Auth            | python-jose + passlib/bcrypt  |
| Validation      | Pydantic v2 + pydantic-extra-types |
| Logging         | Loguru                        |
| Date parsing    | dateparser                    |
| CSV encoding    | chardet                       |
| IDs             | shortuuid                     |

## Data Models

All monetary amounts and energy values are stored as **integers representing 1/100 units** (e.g. `2500` = 25.00 kWh, `44` = €0.44).

### Car

| Field              | Type        | Notes                        |
|--------------------|-------------|------------------------------|
| `name`             | string      | Display name                 |
| `make`             | string?     | Manufacturer                 |
| `model`            | string?     | Model name                   |
| `color`            | string      | Hex color (`#rrggbb`)        |
| `odometer`         | int         | Current odometer (km)        |
| `battery_capacity` | int         | Usable capacity (kWh)        |

### CPO (Charge Point Operator)

| Field           | Type    | Notes                          |
|-----------------|---------|--------------------------------|
| `name`          | string  | Network or charger name        |
| `default_price` | int     | Default price per kWh (1/100)  |

### Charge

| Field           | Type       | Notes                                         |
|-----------------|------------|-----------------------------------------------|
| `date`          | datetime   | Timezone-aware UTC                            |
| `car_id`        | string     | Reference to car                              |
| `car_odometer`  | int        | Odometer reading after charging               |
| `car_soc_after` | int?       | State of charge 0–100% after session          |
| `kwh_charged`   | int        | Energy charged (1/100 kWh)                   |
| `cpo_id`        | string     | Reference to CPO                              |
| `price_total`   | int?       | Total session cost (1/100 currency)           |
| `charge_type`   | string     | `"AC"` or `"DC"`                              |
| `note`          | string?    | Free-text note                                |
| `price_per_kwh` | int        | Computed: price_total / kwh_charged (1/100)  |

## API Reference

All endpoints (except auth) require a `Authorization: Bearer <token>` header.

The interactive Swagger UI is served at `/docs` when the server is running.

### Authentication — `/users`

| Method | Path              | Description                                   |
|--------|-------------------|-----------------------------------------------|
| POST   | `/users/register` | Register a new user (first user = admin)      |
| POST   | `/users/token`    | Log in; returns JWT access token              |
| GET    | `/users/me`       | Get the currently authenticated user          |

### Cars — `/car`

| Method | Path        | Description              |
|--------|-------------|--------------------------|
| GET    | `/car`      | List all cars            |
| POST   | `/car`      | Create a car             |
| GET    | `/car/{id}` | Get a car by ID          |
| PUT    | `/car/{id}` | Update a car             |
| DELETE | `/car/{id}` | Delete a car             |

### Charge Point Operators — `/cpo`

| Method | Path        | Description              |
|--------|-------------|--------------------------|
| GET    | `/cpo`      | List all CPOs            |
| POST   | `/cpo`      | Create a CPO             |
| GET    | `/cpo/{id}` | Get a CPO by ID          |
| PUT    | `/cpo/{id}` | Update a CPO             |
| DELETE | `/cpo/{id}` | Delete a CPO             |

### Charges — `/charge`

| Method | Path                    | Description                                         |
|--------|-------------------------|-----------------------------------------------------|
| GET    | `/charge`               | List charges (supports `limit`, `offset`, `timespan`, `from_date`, `to_date`) |
| POST   | `/charge`               | Create a charge record                              |
| GET    | `/charge/{id}`          | Get a charge by ID                                  |
| PUT    | `/charge/{id}`          | Update a charge                                     |
| DELETE | `/charge/{id}`          | Delete a charge                                     |
| POST   | `/charge/csv_import`    | Bulk import from CSV file                           |

#### Time-range filtering

The `GET /charge` endpoint accepts flexible time filters:

- `timespan=7d` — charges from the last 7 days (supports `d`, `w`, `h`, `m`, `s`)
- `from_date=2024-01-01T00:00:00Z&to_date=2024-12-31T23:59:59Z` — explicit range

## Configuration

Create a `.env` file in `backend/` (or set environment variables directly):

```env
MONGODB_URL=mongodb://localhost:27017/chargelogger
API_SECRET_KEY=<generate a random secret>
API_ALGORITHM=HS256
API_ACCESS_TOKEN_EXPIRE_MINUTES=129600
```

| Variable                          | Required | Default  | Description                    |
|-----------------------------------|----------|----------|--------------------------------|
| `MONGODB_URL`                     | Yes      | —        | MongoDB connection string       |
| `API_SECRET_KEY`                  | Yes      | —        | Secret used to sign JWT tokens  |
| `API_ALGORITHM`                   | No       | `HS256`  | JWT signing algorithm           |
| `API_ACCESS_TOKEN_EXPIRE_MINUTES` | No       | `129600` | Token lifetime (90 days)        |

## Setup & Running

### Prerequisites

- Python 3.12
- [`uv`](https://github.com/astral-sh/uv) (fast Python package manager)
- [`mise`](https://mise.jdx.dev/) (optional task runner)
- A running MongoDB instance (or use Docker Compose from the repo root)

### Install dependencies

```bash
cd backend
uv sync
```

### Run the development server

```bash
# Using mise
mise run run

# Or directly
python app/main.py
```

The API listens on `http://0.0.0.0:8000` by default.

### Run with Docker Compose

From the repository root:

```bash
docker-compose up api mongo
```

## Testing

The test suite uses `pytest` and an in-memory MongoDB instance (no external database required).

```bash
# Using mise
mise run test

# Or directly
pytest
```

Test files live in `tests/` and cover authentication, car CRUD, CPO CRUD, and charge logic including odometer validation and CSV import.

## CSV Import

`POST /charge/csv_import?car=<car_id>` accepts a `multipart/form-data` upload.

Expected columns (order flexible, headers required):

| Column        | Format                              | Notes                             |
|---------------|-------------------------------------|-----------------------------------|
| `date`        | `DD.MM.YYYY HH:MM` or similar       | Parsed with dateparser (DMY bias) |
| `odometer`    | integer or decimal                  | Kilometres                        |
| `kwh`         | decimal (`.` or `,` separator)      | kWh charged                       |
| `price`       | decimal                             | Total session cost                |
| `cpo`         | string                              | CPO name; created if not found    |
| `type`        | `AC` / `DC`                         |                                   |
| `note`        | string                              | Optional                          |

Additional import behaviour:
- Character encoding is detected automatically (UTF-8, ISO-8859-1, etc.)
- Duplicate timestamps are shifted by 1 second to avoid collisions
- Per-row error reporting in the response JSON
- Pass `delimiter=;` for semicolon-separated files
