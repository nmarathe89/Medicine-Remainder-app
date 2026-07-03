# Decisions Made Under Ambiguity (for review)

Per the instruction to make and document my own decisions where the brief was
ambiguous or silent.

## 1. Frontend framework: Next.js (React)
The brief asked for "ReactJS as UI" with "server and client architecture."
**Decision:** use **Next.js 15 (App Router)** — it is React and natively
provides the server (SSR) + client component split requested. Server components
reach the backend over the internal network; client components call the public
REST API and hold the session token.

## 2. Browser notifications: in-app polling + toasts
Constraint: all alerts on the browser, no email/SMS. Options were polling,
WebSockets, or Web Push. **Decision (confirmed with user):** short-interval
**polling** of `/api/alerts/due` rendering toasts. Simplest, identical behaviour
local and on Cloud Run (which has WebSocket/connection constraints), no service
worker or push infrastructure.

## 3. Alert model = materialized rows
The original app scheduled OS notifications directly. **Decision:** materialize
each dose as an `alerts` row (`pending → sent → taken/skipped`). This makes
"alerts sent so far" and "upcoming in 48h" (admin dashboard) simple counts, and
gives the browser something concrete to poll and acknowledge. Alerts are
generated for the next ~3 days on medicine creation.

## 4. "Sent" alert semantics
**Decision:** an alert counts as *sent* once its scheduled time passes and the
polling endpoint transitions it (`sent`), and it remains counted after being
acknowledged (`taken`/`skipped`). The admin "Alerts Sent" total therefore counts
`sent + taken + skipped`.

## 5. Admin dashboard windows
The brief specified the metrics but not exact windows. **Decisions:** feedback
counts use a **rolling 12 months**; user trend uses **37 monthly buckets** (36
months + current, pre-seeded to zero so the line chart is continuous);
"upcoming alerts" uses a **48-hour** window as specified.

## 6. Admin account provisioning
The brief wanted an admin login but no admin self-registration flow.
**Decision:** admin accounts are created via **seed data** (seeded admin:
`admin / admin123`). Public registration always creates a normal `user`. This
avoids a privilege-escalation path in the open registration endpoint.

## 7. Time handling
The original hard-coded `Asia/Kolkata`. **Decision:** store and compute all
times in **UTC** on the backend; the browser renders in the viewer's local time.
A `_naive()` helper normalizes datetimes so the identical code path works on
PostgreSQL (aware) and the SQLite test DB (naive).

## 8. Test database
**Decision:** tests run against **in-memory SQLite** (shared `StaticPool`) so the
suite runs anywhere with no external services, while the *same application code*
runs on PostgreSQL in Compose/Cloud. The DB URL is the only thing that changes.

## 9. Python version (local vs container)
Container target is `python:3.14-slim` as instructed. Local development machine
had Python 3.13; the code uses no 3.14-only features, so tests were executed on
3.13 and are fully compatible with 3.14.

## 10. Residual npm advisory (accepted risk)
`npm audit` reports 2 **moderate** advisories via a transitive **postcss** used
by Next's build toolchain (`GHSA-qx2v-qp2m-jg93`, a build-time stringify XSS).
The only automated "fix" is downgrading Next to 9.3.3 — an unacceptable breaking
downgrade that reintroduces far more serious issues. **Decision:** stay on the
**patched Next 15.5.20** (the original 15.1.3 had a real runtime CVE, now
resolved) and accept the low-severity, build-time-only postcss advisory. Revisit
when Next ships an updated bundled postcss.

## 11. Password policy
**Decision:** minimal but enforced (username ≥3, password ≥4) to keep the demo
usable while still exercising validation. Tighten for production.

## 12b. Dependency pinning strategy (Python 3.14)
Initial exact version pins predated Python 3.14 and had no prebuilt wheels,
causing the Docker build to fail compiling `pydantic-core`/`psycopg` from
source. **Decision:** use bounded **version ranges** in `requirements.txt` so
pip selects 3.14-compatible builds while staying within a stable major range.
Verified: image builds and the 23-test suite still passes on the upgraded set.

## 12c. Local DB host port
Port 5432 commonly clashes with a developer's existing Postgres. **Decision:**
the compose DB publishes on host port **5433** by default (configurable via
`DB_HOST_PORT`); the container port and backend `DATABASE_URL` remain 5432.

## 13. Scope boundary
Per the brief, **cloud deployment and testing are out of scope.** Cloud-ready
artifacts (Dockerfiles honoring `$PORT`, Secret Manager integration behind
`APP_ENV=cloud`, topology docs) are provided but not deployed.
