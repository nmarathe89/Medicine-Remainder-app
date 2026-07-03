# New Architecture — Local Execution (Docker Compose)

Three containers on one Docker network, started with `docker compose up`. The
same images are what deploy to the cloud, so behaviour is consistent.

```mermaid
flowchart LR
    Browser["🌐 Browser<br/>(multiple users / tabs = multiple sessions)"]

    subgraph Compose["Docker Compose network"]
        FE["frontend<br/>Next.js 15 / React 19<br/>node:22-slim · :3000<br/>(SSR server + client)"]
        BE["backend<br/>FastAPI · python:3.14-slim · :8000<br/>REST API + JWT auth"]
        DB[("db<br/>PostgreSQL 17 · :5432<br/>volume: pgdata")]
    end

    Browser -->|"HTTP :3000<br/>(client REST via NEXT_PUBLIC_API_BASE_URL)"| FE
    Browser -->|"REST/JSON :8000"| BE
    FE -->|"SSR calls<br/>INTERNAL_API_BASE_URL=http://backend:8000"| BE
    BE -->|"SQLAlchemy<br/>DATABASE_URL=postgresql+psycopg://db:5432"| DB

    BE -.->|"polling GET /api/alerts/due<br/>drives in-browser toasts"| Browser

    Config["APP_ENV=local<br/>secrets from .env (gitignored)<br/>SEED_ON_STARTUP=true"]
    Config -.-> BE
```

## Flow
1. `docker compose up --build` starts **db**, then **backend** (waits for DB
   healthcheck), then **frontend**.
2. On startup the backend creates tables (`init_db`) and loads **synthetic seed
   data** (idempotent).
3. The browser loads the Next.js UI; client components call the backend REST API
   directly; server components can call it over the internal network.
4. Reminders are surfaced by the client **polling** `/api/alerts/due` every ~15s
   and rendering toasts — no email/SMS.

## Environment variables (local)
| Var | Value | Purpose |
|-----|-------|---------|
| `APP_ENV` | `local` | Skip Secret Manager; use env secrets |
| `DATABASE_URL` | `...@db:5432/mediminder` | Points at compose Postgres |
| `JWT_SECRET` | dev placeholder | JWT signing |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Browser → backend |
| `INTERNAL_API_BASE_URL` | `http://backend:8000` | SSR → backend |
```
