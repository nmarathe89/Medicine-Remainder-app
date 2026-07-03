# New Tech Stack — Local Execution Architecture

Everything runs via **`docker compose up`** on the developer's machine. Three
containers, one shared network, one persistent volume for the database.

## Tech stack (local)

| Layer            | Image / library                                          |
|------------------|----------------------------------------------------------|
| Database         | `postgres:17-alpine`                                     |
| Backend API      | `python:3.14-slim` + FastAPI + SQLAlchemy + Uvicorn      |
| Auth             | JWT (HS256), bcrypt-hashed passwords                     |
| WebSocket alerts | FastAPI WebSocket endpoint (`/ws/alerts/{user_id}`)      |
| Scheduler        | APScheduler (in-process; runs inside the API container)  |
| Frontend server  | `node:22-slim` + Express SSR                             |
| Frontend client  | React 18 + Vite build + Recharts (dashboard)             |
| Reverse proxy    | *not needed locally* — direct ports on `localhost`       |
| Secrets          | `.env` file (git-ignored) mounted into containers        |

## Component diagram

```
                  Developer's browser
                  ─────────────────────
                          │
                  http://localhost:3000
                          ▼
        ┌───────────────────────────────────────┐
        │  frontend (node:22-slim)              │
        │  ┌─────────────────────────────────┐  │
        │  │ Express SSR server (server.js)  │  │
        │  │  - renders React shell          │  │
        │  │  - serves /assets bundle        │  │
        │  │  - injects window.__CONFIG__    │  │
        │  └───────────────┬─────────────────┘  │
        │                  │                    │
        │           React client (hydrated)     │
        │           - Recharts dashboard        │
        │           - fetch → /api/*            │
        │           - WebSocket → /ws/alerts    │
        └──────────────────┬────────────────────┘
                           │
                  http://backend:8000 (in-network)
                  http://localhost:8000 (host)
                           ▼
        ┌───────────────────────────────────────┐
        │  backend (python:3.14-slim)           │
        │  ┌─────────────────────────────────┐  │
        │  │ FastAPI  (uvicorn)              │  │
        │  │  /api/auth  /api/medicines      │  │
        │  │  /api/alerts /api/feedback      │  │
        │  │  /api/admin/*                   │  │
        │  │  /ws/alerts/{user_id}           │  │
        │  └───────────────┬─────────────────┘  │
        │  ┌───────────────▼─────────────────┐  │
        │  │ APScheduler tick every 30 s     │  │
        │  │  - materializes due alerts      │  │
        │  │  - broadcasts via WebSocket     │  │
        │  └─────────────────────────────────┘  │
        │  ┌─────────────────────────────────┐  │
        │  │ SQLAlchemy → asyncpg            │  │
        │  └───────────────┬─────────────────┘  │
        └──────────────────┼────────────────────┘
                           ▼
        ┌───────────────────────────────────────┐
        │  db  (postgres:17-alpine)             │
        │  volume: pgdata                       │
        │  db name: mediminder                  │
        └───────────────────────────────────────┘

  Config source: .env (git-ignored)
  ENVIRONMENT=local
  DATABASE_URL=postgresql+asyncpg://mediminder:mediminder@db:5432/mediminder
  JWT_SECRET=<local-dev-value>
```

## How the SAME code runs locally and on cloud

`backend/app/config.py` reads one variable: **`ENVIRONMENT`**.

| Value    | Config source                                          |
|----------|--------------------------------------------------------|
| `local`  | Environment variables from `.env`                      |
| `cloud`  | Google Secret Manager (`projects/645869155931/secrets/serviceaccount`) |

Everything downstream — database URL, JWT secret, admin bootstrap password —
is looked up through the same `get_settings()` function. See
`ARCHITECTURE_CLOUD.md` for the cloud path.

## Running it

```bash
cd mediminder-web
cp .env.example .env          # optional; sensible defaults exist
docker compose up --build
# Frontend: http://localhost:3000
# Backend docs: http://localhost:8000/docs
# Seed data: docker compose exec backend python -m app.seed
```
