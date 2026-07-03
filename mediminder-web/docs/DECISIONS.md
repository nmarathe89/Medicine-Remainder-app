# Decisions & Rationale

Every ambiguity in the task, and how I resolved it. Reviewable end-of-project.

## D-01. Where the new project lives

The original Flutter code is kept intact at the repo root. All new work lives
under **`mediminder-web/`** so both stacks can coexist in the same repo and
the diff is easy to review. Nothing under `lib/`, `android/`, `ios/`, etc.
was modified.

## D-02. Database

**PostgreSQL 17** (as requested), via SQLAlchemy 2 async + asyncpg. The
`postgres:17-alpine` image is the smallest official variant and stays inside
the "slim / alpine" spirit called for by the security instruction.

## D-03. Backend framework

**FastAPI 0.115** on Uvicorn (async), targeting `python:3.14-slim`. Chosen
because the spec explicitly names FastAPI, and because its automatic OpenAPI
docs (at `/docs`) make it trivial to demo the API.

## D-04. Password hashing

Switched from `bcrypt` to **pbkdf2_sha256** (still via passlib). Rationale:
`bcrypt` has a hard 72-byte input limit and the installed bcrypt version
had a passlib incompatibility on the test box (see failed test run in
history). pbkdf2_sha256 is FIPS-approved, has no length limit, and needs
no C extension — it also builds inside `python:3.14-slim` without extra
apt packages. For a production deploy, consider argon2.

## D-05. Session storage & multi-session support

JWTs are stateless, but the spec required multi-session AND we needed a way
to revoke individual sessions. Compromise: every JWT carries a `jti` and a
row is written to the `sessions` table. Auth requires both the JWT to
verify AND the row to still exist. Concurrent sessions per user are
naturally supported — nothing prevents multiple `sessions` rows.

## D-06. Notification transport

**WebSocket + browser Notification API**. The spec forbids email/SMS. The
scheduler pushes JSON to `/ws/alerts` and the React app shows a toast
(always) plus a native browser notification (if the user granted
permission). This keeps the delivery path server-driven without polling.

## D-07. Scheduler

**APScheduler in-process** rather than Celery / Cloud Tasks. Rationale: one
container is enough for the demo scale; adding Redis + Celery would triple
the moving parts. For Cloud Run we pin `min-instances=1` on the backend so
the scheduler survives — documented in `ARCHITECTURE_CLOUD.md`. If load grows,
migrating to Cloud Scheduler + Pub/Sub is a straight lift.

## D-08. Alert materialization

Alerts are pre-computed for a rolling **48-hour horizon** (matches the
dashboard's "upcoming in 48h" panel). The scheduler tick (every 30s) both
tops up the horizon AND delivers due alerts. Idempotent by design — running
the tick twice never double-inserts.

## D-09. Frontend structure — "server and client architecture"

Interpreted as an **Express SSR server** that serves the built React bundle
and proxies API/WebSocket calls, giving the browser a same-origin surface
in both local and cloud modes. This also gives us **runtime config injection**
(via `window.__CONFIG__`) so the SAME image can point at different backends
without a rebuild.

## D-10. Base images

`python:3.14-slim` and `node:22-slim` (as instructed). Both are current
stable slim variants at the time of writing. Multi-stage builds keep the
final image lean.

## D-11. Secrets

- **Local**: `.env` file (git-ignored) → docker-compose reads it.
- **Cloud**: Secret Manager JSON blob at
  `projects/645869155931/secrets/serviceaccount`, fetched once at process
  start by `app/config.py`. No secret is written to disk or logged.
- **Git**: only `.env.example` is committed with placeholder values.

## D-12. Admin account bootstrapping

On first boot the backend creates a user with `is_admin=true` from
`ADMIN_USERNAME` / `ADMIN_PASSWORD` env vars. In cloud mode those values
come from Secret Manager, so no default admin password ever lives on disk.

## D-13. Test database

Tests use **in-memory SQLite via aiosqlite** so `pytest` runs on a laptop
with zero infrastructure. The app code doesn't branch on database type —
SQLAlchemy handles the compatibility. The one place we cared (SQL
`date_trunc` in the admin dashboard) was rewritten to bucket in Python,
which now works for both databases and has no material perf impact at
this scale.

## D-14. Timezone handling

The original app hard-coded `Asia/Kolkata`. The rewrite stores all
timestamps as UTC in Postgres, and the browser renders in the viewer's
local timezone via `Date#toLocaleString()`. Simpler, no server-side
timezone puzzles.

## D-15. Synthetic data volume

Seeder creates **24 users, ~70 medicines, ~200 alerts, ~50 feedback rows**
— total DB dump is a few hundred KB, well under the "kilobytes only" rule.
No PII beyond fake usernames/emails at `@mediminder.local`.

## D-16. What was NOT deployed to GCP

Per the task's `<out of scope>` clause, `gcloud` is never invoked. The
`deploy/` manifests were validated syntactically and reviewed but not
applied. `README` calls this out explicitly so a human deployer isn't
surprised.

## D-17. Original Flutter code

Left in place. It is *not* the deliverable; the deliverable is the new
`mediminder-web/` stack. Keeping the original in the same repo makes the
"before" side of the ARCHITECTURE_ASIS diagram directly clickable.

## D-19. Base Python image is 3.13-slim, not 3.14-slim

The security instruction called for "latest stable slim" images. My first
pass used `python:3.14-slim`, but the docker build failed:

```
error: the configured Python interpreter version (3.14) is newer than
       PyO3's maximum supported version (3.13)
ERROR: Failed building wheel for pydantic-core
```

`pydantic-core` and `asyncpg` do not yet publish cp314 wheels, and their
PyO3-based sdist can't compile against Python 3.14. Options considered:

1. Add the full Rust toolchain to the builder stage. Rejected: ~500 MB of
   build deps, brittle every time PyO3 gains 3.14 support and the flag
   flips.
2. Drop to `python:3.13-slim`. Chosen. Current stable slim (Python 3.13 is
   still the newest release with mature wheel coverage), no known CVEs in
   the CVE database as of build date, and all pins install as pre-built
   wheels — build completes in seconds.

Also affected the app's `PYTHONPATH` (now `python3.13` site-packages).
When wheel coverage catches up, flip both `FROM` lines and the PYTHONPATH
back to 3.14; no other code changes needed.

## D-20. Docker host ports are configurable

First bring-up on the target machine collided with an existing service
holding 3000, 5432, 5433, and 8000. Fix: docker-compose exposes
`FRONTEND_HOST_PORT` and `BACKEND_HOST_PORT` env vars (defaults 3000 and
8000). The DB port is not published to the host by default at all — the
backend reaches it over the compose network. Documented in the compose
file inline and in `.env.example`.

## D-21. Frontend proxy pathRewrite

`http-proxy-middleware` v3 strips the mount prefix (Express `app.use`
behavior). Fixed by adding `pathRewrite: (path) => \`/api${path}\`` (and
the same for `/ws`) so the backend receives the full path it expects.
Verified end-to-end: `curl http://localhost:3001/api/health` → 200 from
the backend behind the proxy.

## D-18. Warning cleanup deferred

Test output has 21 upstream deprecation warnings (passlib/jose using
`datetime.utcnow()`, FastAPI's `@app.on_event`, pydantic v1-style `Config`).
None affect correctness. Migrating to `datetime.now(UTC)`, the lifespan API,
and `ConfigDict` is a follow-up.
