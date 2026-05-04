# pyro-risk-api

FastAPI service that exposes Pyronear cameras enriched with a daily fire-risk
score. Cameras are pulled from the upstream
[pyronear/pyro-api](https://github.com/pyronear/pyro-api) on startup and
refreshed every night at 02:00 Europe/Paris. For each camera, the current-day
[FWI (Fire Weather Index)](https://effis.jrc.ec.europa.eu/about-effis/technical-background/fire-danger-forecast)
is sampled from the Copernicus EFFIS WMS layer (`mf010.fwi`, Météo-France 10 km).

## Endpoints

| Method | Path                  | Auth   | Description                              |
|--------|-----------------------|--------|------------------------------------------|
| GET    | `/health`             | none   | Liveness probe                           |
| GET    | `/cameras`            | basic  | List all cameras with current FWI        |
| GET    | `/cameras/{id}`       | basic  | Single camera by id                      |
| GET    | `/docs`               | none   | OpenAPI / Swagger UI                     |

Each camera payload:

```json
{
  "id": 1,
  "name": "mateo-camera-01",
  "organization_id": 2,
  "lat": 48.4267,
  "lon": 2.7109,
  "fwi": 0.0,
  "fwi_class": "very_low",
  "last_refresh_at": "2026-05-04T15:32:05Z"
}
```

`fwi_class` follows the EFFIS European danger classes: `very_low`, `low`,
`moderate`, `high`, `very_high`, `extreme`.

## Configuration

All settings are read from environment variables (or a local `.env` file —
not committed). See `.env.example`:

| Variable                       | Description                                   | Default                              |
|--------------------------------|-----------------------------------------------|--------------------------------------|
| `API_USERNAME`                 | Basic-auth user for protected routes          | _required_                           |
| `API_PASSWORD`                 | Basic-auth password for protected routes      | _required_                           |
| `PYRO_API_HOST`                | Upstream pyro-api host                        | `https://alertapi.pyronear.org/`     |
| `PYRO_API_USERNAME`            | Upstream pyro-api username                    | _required_                           |
| `PYRO_API_PASSWORD`            | Upstream pyro-api password                    | _required_                           |
| `CAMERAS_REFRESH_CRON_HOUR`    | Daily refresh hour                            | `2`                                  |
| `CAMERAS_REFRESH_CRON_MINUTE`  | Daily refresh minute                          | `0`                                  |
| `CAMERAS_REFRESH_TIMEZONE`     | IANA timezone for the schedule                | `Europe/Paris`                       |

The `/cameras` endpoints are protected with HTTP Basic auth; `/health` is left
public so container orchestrators can probe it.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env  # then fill in credentials
uvicorn pyro_risk_api.main:app --reload
```

Then:

```bash
curl http://127.0.0.1:8000/health
curl -u admin:changeme http://127.0.0.1:8000/cameras
```

## Run with Docker

```bash
docker compose up --build
```

Or build and run manually:

```bash
docker build -t pyro-risk-api .
docker run --rm -p 8000:8000 --env-file .env pyro-risk-api
```

The image is multi-stage (Python 3.12 slim), runs as a non-root user, and
ships a `HEALTHCHECK` hitting `/health`.

## Project layout

```
pyro_risk_api/
├── main.py              # FastAPI app, lifespan, APScheduler job
├── api/
│   ├── health.py        # GET /health
│   └── cameras.py       # GET /cameras, GET /cameras/{id} (auth-protected)
└── core/
    ├── config.py        # pydantic-settings, .env loader
    ├── auth.py          # Basic-auth dependency
    ├── pyro_client.py   # Upstream pyro-api login + client factory
    └── fwi.py           # EFFIS WMS sampling, FWI class buckets
```

## How the refresh works

1. On startup the lifespan calls `refresh_cameras(app)`:
   - Logs in to `PYRO_API_HOST` via `POST /api/v1/login/creds`.
   - Calls `pyroclient.Client.fetch_cameras()`.
   - For each camera, samples today's FWI from EFFIS and stores
     `(id, name, organization_id, lat, lon, fwi, fwi_class, last_refresh_at)`
     in `app.state.cameras`.
2. An `AsyncIOScheduler` (APScheduler) re-runs the same function every day at
   the configured hour/minute in the configured timezone.
3. The HTTP routes are pure reads from `app.state.cameras` — no upstream calls
   on the request path.
