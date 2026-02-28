# Charge Logger — Frontend

Streamlit web UI for the Chargelogger backend. Provides an interactive dashboard for browsing, editing, and analysing EV charging sessions across multiple vehicles.

## Features

- **Car selector** — switch between vehicles in the sidebar; each car's data loads independently
- **Charge table** — paginated, sortable table of all sessions with calculated distance and per-kWh cost columns
- **Inline editing** — enable edit mode to add, modify, or delete rows; a review dialog shows a diff before saving
- **Statistics** — monthly, yearly, and all-time summaries covering total distance, total cost, cost per 100 km, and efficiency (kWh/100 km); year-on-year delta view for all-time mode
- **Charging distribution** — pie chart and metrics for AC vs DC session breakdown
- **CPO management** — create new Charge Point Operators and edit their name or default price directly from the sidebar
- **Persistent sessions** — JWT token stored in browser cookies so login survives page refreshes (90-day expiry)

## Tech Stack

| Component          | Library / Version                    |
|--------------------|--------------------------------------|
| Framework          | Streamlit >= 1.43                    |
| Data manipulation  | Pandas >= 2.2                        |
| Charts             | Plotly >= 6.0                        |
| HTTP client        | Requests >= 2.32                     |
| Session cookies    | streamlit-cookies-controller >= 0.0.4|
| Logging            | Loguru                               |

## UI Overview

### Sidebar

- **Car dropdown** — select the active vehicle
- **Timeframe radio** — filter data: *Last month*, *Last year* (default), or *All time*
- **CPO dropdown + Edit** — view and edit an existing CPO's details
- **Add CPO button** — opens a dialog to create a new operator
- **Logged-in user** and **Logout** button

### Main Area

| Section                  | Description                                                         |
|--------------------------|---------------------------------------------------------------------|
| Car info                 | Name, make/model, colour swatch, odometer, battery capacity         |
| Charges table            | All sessions for the selected car and timeframe; editable           |
| Statistics               | Aggregated totals and per-100-km metrics for the selected timeframe |
| Charging distribution    | AC/DC pie chart with totals and ratio metric                        |

### Edit Mode

Toggle *Allow editing* above the charge table to:

- **Edit** any cell (date, odometer, kWh, price, CPO, type, note)
- **Add** a new row at the top
- **Delete** one or more rows

All pending changes are batched and shown in a confirmation dialog before being sent to the backend.

## Configuration

| Variable                | Default                  | Description                       |
|-------------------------|--------------------------|-----------------------------------|
| `CHARGELOGGER_BACKEND`  | `http://localhost:8000`  | Base URL of the Chargelogger API  |

The backend URL can also be passed as the first positional argument to `streamlit run`.

## Setup & Running

### Prerequisites

- Python 3.12
- [`uv`](https://github.com/astral-sh/uv) (fast Python package manager)
- [`mise`](https://mise.jdx.dev/) (optional task runner)
- A running instance of the Chargelogger backend

### Install dependencies

```bash
cd frontend
uv sync
```

### Run the development server

```bash
# Using mise
mise run run

# Or directly (backend defaults to http://localhost:8000)
streamlit run main.py

# With a custom backend URL
streamlit run main.py http://api.example.com:8000

# Or via environment variable
CHARGELOGGER_BACKEND=http://api.example.com:8000 streamlit run main.py
```

The UI is available at **http://localhost:8501**.

### Run with Docker Compose

From the repository root (starts the backend, MongoDB, and frontend together):

```bash
docker-compose up
```

## Authentication

1. Open the UI and enter your username and password.
2. On success the JWT token is stored in a browser cookie.
3. Subsequent page loads restore the session automatically from the cookie.
4. The token expires after 90 days (configurable on the backend via `API_ACCESS_TOKEN_EXPIRE_MINUTES`).
5. Use the **Logout** button in the sidebar to clear the cookie and end the session.
