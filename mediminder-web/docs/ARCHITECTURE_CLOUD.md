# New Tech Stack — Google Cloud Platform Architecture

Same containers, different runtime. Managed database, managed secrets,
managed HTTPS via Cloud Run.

## Tech stack (cloud)

| Layer            | GCP service                                              |
|------------------|----------------------------------------------------------|
| Database         | Cloud SQL for PostgreSQL 17                              |
| Backend API      | Cloud Run (container `backend`)                          |
| Frontend         | Cloud Run (container `frontend`)                         |
| Container images | Artifact Registry                                        |
| Secrets          | Secret Manager (`projects/645869155931/secrets/serviceaccount`) |
| Build            | Cloud Build (`deploy/cloudbuild.yaml`)                   |
| DNS / TLS        | Cloud Run built-in `*.run.app` (or Cloud Load Balancer)  |
| Egress to DB     | Cloud SQL Auth Proxy sidecar (built into Cloud Run)      |

## Component diagram

```
                          User (browser)
                                │
                                ▼
                    ┌──────────────────────┐
                    │  Cloud Load Balancer │ (optional custom domain)
                    │       + HTTPS        │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Cloud Run: frontend │
                    │  node:22-slim + SSR  │
                    │  env FRONTEND_ORIGIN │
                    │      API_BASE_URL    │
                    └──────────┬───────────┘
                               │  REST + WebSocket
                               ▼
                    ┌──────────────────────┐
                    │  Cloud Run: backend  │
                    │  python:3.14-slim    │
                    │  env ENVIRONMENT=cloud
                    │      GCP_PROJECT=... │
                    │      SECRET_NAME=projects/645869155931/secrets/serviceaccount
                    └──┬────────────────┬──┘
                       │                │
                       │                └─► fetch DB creds + JWT secret
                       │                     from Secret Manager on startup
                       ▼
                    ┌──────────────────────┐
                    │  Secret Manager      │
                    │  projects/645869155931│
                    │   /secrets/serviceaccount
                    │   (JSON blob:        │
                    │    { db_password,    │
                    │      jwt_secret,     │
                    │      admin_password })
                    └──────────────────────┘
                       │
                       ▼
                    ┌──────────────────────┐
                    │  Cloud SQL           │
                    │  postgres 17         │
                    │  instance: mediminder│
                    │  private IP + IAM DB │
                    │  auth                │
                    └──────────────────────┘

  Build & deploy pipeline
  ────────────────────────
  git push branchb ──► Cloud Build trigger
                        ├─ docker build backend  → Artifact Registry
                        ├─ docker build frontend → Artifact Registry
                        ├─ gcloud run deploy backend  --image ...
                        └─ gcloud run deploy frontend --image ...
```

## Same code — differences at boundaries only

- **`app/config.py`** — when `ENVIRONMENT=cloud`, fetches the Secret Manager
  blob once at process start and populates `Settings` in-memory. Never writes
  secrets to disk. In `local` mode, `.env` is used instead.
- **Database URL** — locally `db:5432`; on cloud, the Cloud SQL Auth Proxy
  side-container exposes `127.0.0.1:5432` inside the Cloud Run instance. The
  URL is still `postgresql+asyncpg://.../mediminder`; only the host changes.
- **Notifications** — always in-browser (WebSocket toast + Notification API).
  Identical between environments; no SMS/email service to wire up.
- **Scheduler** — APScheduler runs in-process. Cloud Run keeps `min-instances=1`
  for the backend so the scheduler is always alive. (Out-of-scope: for higher
  scale, we would move it to Cloud Scheduler + Pub/Sub.)

## Cost-conscious defaults

- Both Cloud Run services: 512 MiB, min-instances=1 (backend), min-instances=0 (frontend), max-instances=3.
- Cloud SQL: `db-f1-micro`, private IP, backups off (dev/demo tier).
- Region: `asia-south1` (matches the original app's IST timezone).

## What is intentionally NOT wired up (per `<out of scope>`)

- The actual `gcloud` deploy is not executed. Manifests (`deploy/cloudbuild.yaml`,
  `deploy/cloud-run-*.yaml`) are provided and validated syntactically only.
- No custom domain / Cloud LB is provisioned; teams can layer that later.
