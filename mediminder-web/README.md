# Mediminder — Web Edition

Container-native rewrite of the original Flutter Medicine Reminder app.
PostgreSQL 17 + Python 3.14 + FastAPI backend, React 18 + Express SSR
frontend, browser-only notifications via WebSocket. Runs unchanged locally
via `docker compose up`, and on Google Cloud Platform via the manifests in
`deploy/`.

## Quick start (local)

```bash
cd mediminder-web
cp .env.example .env         # tweak JWT_SECRET / ADMIN_PASSWORD if you like
docker compose up --build

# Open the app:
#   http://localhost:3000        (React + Express SSR)
#   http://localhost:8000/docs   (FastAPI Swagger UI)
#   http://localhost:8000/api/health

# Optional — populate synthetic data for the admin dashboard:
docker compose exec backend python -m app.seed
```

If ports 3000 or 8000 are already taken on your host, override with:

```bash
BACKEND_HOST_PORT=8001 FRONTEND_HOST_PORT=3001 docker compose up --build
# then browse http://localhost:3001
```

The Postgres port is intentionally not published to the host by default —
the backend talks to the DB over the internal docker network. If you want
`psql`/GUI access, uncomment the `ports:` line under the `db` service in
`docker-compose.yml`.

Default admin credentials in local mode: **`admin` / `admin123`** (from
`.env`). Change them before any real use.

## Running the backend tests

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
# 16 passed, ~1.3s. Uses in-memory SQLite; no docker required.
```

See `docs/TEST_RESULTS.md` for the captured output.

## Repository layout

```
mediminder-web/
├── backend/            FastAPI service (python:3.14-slim)
│   ├── app/
│   │   ├── config.py       env-vs-Secret-Manager settings
│   │   ├── database.py     async SQLAlchemy engine + init_models
│   │   ├── main.py         FastAPI app + APScheduler
│   │   ├── models/         User, Medicine, Alert, Feedback, Session
│   │   ├── routers/        auth, medicines, alerts (+ WS), feedback, admin
│   │   ├── schemas/        pydantic request/response models
│   │   ├── services/       security (JWT/bcrypt), alerts (materialize + push)
│   │   └── seed.py         synthetic-data script
│   ├── tests/           16 pytest tests (auth / medicines / admin)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/           React + Express SSR (node:22-slim)
│   ├── client/          Vite React app (register/login/home/admin/…)
│   ├── server/          Express SSR shell + /api and /ws proxy
│   ├── Dockerfile
│   └── package.json
├── deploy/             Cloud Build + Cloud Run manifests
├── docs/               Architecture, ER, use-cases, test-cases, decisions
├── docker-compose.yml
├── .env.example
└── README.md
```

## Documentation index

- **[docs/ARCHITECTURE_ASIS.md](docs/ARCHITECTURE_ASIS.md)** — the original Flutter app.
- **[docs/ARCHITECTURE_LOCAL.md](docs/ARCHITECTURE_LOCAL.md)** — new stack, local.
- **[docs/ARCHITECTURE_CLOUD.md](docs/ARCHITECTURE_CLOUD.md)** — new stack, GCP.
- **[docs/ER_DIAGRAM.md](docs/ER_DIAGRAM.md)** — entity relationships.
- **[docs/USE_CASES.md](docs/USE_CASES.md)** — actors, use cases, and task list.
- **[docs/TEST_CASES.md](docs/TEST_CASES.md)** — TC-01…TC-16 mapping.
- **[docs/TEST_RESULTS.md](docs/TEST_RESULTS.md)** — pytest transcript.
- **[docs/DECISIONS.md](docs/DECISIONS.md)** — every ambiguity resolution.
- **[deploy/README.md](deploy/README.md)** — GCP deployment guide.

## What the app does

- Register / log in with username + password (multi-session supported).
- Add medicines (name, dosage, type, hour interval, start time).
- See tiles for every active reminder; delete when finished.
- Receive **in-browser toasts + native notifications** at scheduled times.
- Review sent alerts, acknowledge or skip.
- Submit positive / negative feedback.
- Admin dashboard: active/inactive user pie, last-year feedback bar chart,
  3-year signup trend line, sent-alert count, next-48h alert count.

## Security

- No secrets in the repo. `.env` is git-ignored; `.env.example` ships only
  placeholders.
- Passwords stored with pbkdf2_sha256 (see `docs/DECISIONS.md#d-04`).
- JWTs carry a `jti` matched against a `sessions` table for revocation.
- In cloud mode, secrets come from **Secret Manager**
  (`projects/645869155931/secrets/serviceaccount`).
- Only sample synthetic data (KB scale) is ever committed.

## Attribution

Original Flutter app kept unmodified at the repo root for reference.
