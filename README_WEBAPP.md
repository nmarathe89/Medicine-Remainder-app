# Mediminder — Web Application (Python + FastAPI + ReactJS + PostgreSQL)

A containerized re-platform of the original Flutter *Medicine Reminder* app into
a web application with a REST backend, a React (Next.js) server+client UI, a
PostgreSQL database, browser-based alerts, user/admin auth, and an admin
analytics dashboard. Runs identically **locally (Docker Compose)** and is ready
for **Google Cloud Platform** (Cloud Run + Cloud SQL) — cloud deployment itself
is out of scope here.

## Tech stack
- **Backend:** Python 3.14, FastAPI, SQLAlchemy 2, PostgreSQL 17 (`python:3.14-slim`)
- **Frontend:** Next.js 15 / React 19 (server + client), Recharts (`node:22-slim`)
- **Auth:** bcrypt password hashing + JWT session tokens (multi-session)
- **Notifications:** in-browser polling + toasts (no email/SMS)

## Run locally (Docker Compose — recommended)
```bash
cp .env.example .env        # placeholders are fine for local
docker compose up --build
```
- Frontend: http://localhost:3000
- Backend API + docs: http://localhost:8000/docs
- Health: http://localhost:8000/healthz

Synthetic demo data is seeded automatically. Seeded admin: **admin / admin123**.
Register your own user, or log in as a seeded user (e.g. **alice / pass1234**).

## Run the backend tests
```bash
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # (Windows)
# or: python -m venv .venv && .venv/bin/pip install -r requirements.txt  # (Unix)
.venv/Scripts/python -m pytest    # tests use in-memory SQLite; app code is unchanged
```
See `docs/TEST_RESULTS.md` for captured results (23 passing).

## Documentation
- `docs/architecture/as-is-architecture.md` — original Flutter app
- `docs/architecture/new-local-architecture.md` — local Docker topology
- `docs/architecture/new-cloud-architecture.md` — GCP topology
- `docs/architecture/erd.md` — entity relationship diagram
- `docs/use-cases.md` — features → use cases → tasks
- `docs/test-cases.md` — test cases per task
- `docs/DECISIONS.md` — decisions made under ambiguity (for review)

## Security notes
- No secrets are committed. Copy `.env.example` → `.env` (gitignored).
- In cloud, the JWT/service-account secret is read from GCP Secret Manager at
  `projects/645869155931/secrets/serviceaccount` (only when `APP_ENV=cloud`).
- Slim, patched base images are used to reduce vulnerabilities.
- Seed data is synthetic and small (KB).
