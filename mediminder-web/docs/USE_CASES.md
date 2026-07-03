# Use Cases & Tasks

Features were extracted from the as-is Flutter app and expanded to fit a
multi-user web app with an admin dashboard.

## Actors

| Actor       | Description                                                    |
|-------------|----------------------------------------------------------------|
| Guest       | Unauthenticated visitor. Can register or log in.               |
| User        | Registered end user. Manages their own medicines and alerts.   |
| Admin       | Built-in `admin` account. Read-only dashboard access.          |
| Scheduler   | Server process. Materializes alerts and pushes WebSocket toasts. |

## Use cases

### UC-01. Register
- **Preconditions:** none.
- **Trigger:** guest submits `/register`.
- **Main flow:** username / email / password → 201 Created + JWT.
- **Alt flows:** duplicate username → 409; duplicate email → 409.

### UC-02. Log in
- **Preconditions:** account exists and is active.
- **Trigger:** user submits `/login`.
- **Result:** JWT with `is_admin=false`; session row inserted.
- **Alt flows:** wrong password → 401; inactive account → 403.

### UC-03. Admin log in
- **Preconditions:** account exists with `is_admin=true`. Bootstrapped on
  first boot from `ADMIN_USERNAME`/`ADMIN_PASSWORD`.
- **Result:** JWT with `is_admin=true`.

### UC-04. Multiple concurrent sessions
- **Trigger:** same user logs in from two browsers / tabs.
- **Result:** two `sessions` rows; both tokens work; logging out one leaves
  the other valid.

### UC-05. Add a medicine
- **Trigger:** user posts `/api/medicines`.
- **Validations:** unique per-user name, type ∈ {Bottle,Pill,Syringe,Tablet},
  interval ∈ {6,8,12,24}, `start_time` matches `\d{4}`.
- **Side effect:** alerts materialized for the 48-hour lookahead.

### UC-06. Delete a medicine
- **Trigger:** user DELETEs `/api/medicines/{id}`.
- **Result:** soft-deletes the row (`is_deleted=true`); pending future alerts
  are ignored by the scheduler because the medicine no longer appears in the
  "active" query.

### UC-07. Receive an in-browser alert
- **Trigger:** scheduler tick finds an alert whose `scheduled_at <= now` and
  `status=pending`.
- **Result:** alert transitions to `sent`, WebSocket pushes a JSON payload,
  the React app shows a toast and optionally a native Notification.

### UC-08. Acknowledge / skip an alert
- **Trigger:** user posts `/api/alerts/{id}/ack` with `acknowledged` or
  `skipped`.
- **Result:** alert row updated; visible in the history page.

### UC-09. Submit feedback
- **Trigger:** user posts `/api/feedback` with positive/negative sentiment.
- **Result:** feedback row created; visible on personal feedback list; feeds
  the admin dashboard yearly aggregate.

### UC-10. Admin dashboard
- **Trigger:** admin GETs `/api/admin/dashboard`.
- **Result:** aggregates for:
  * total users + active/inactive split (pie chart)
  * positive/negative feedback in the last 12 months (bar chart)
  * signups per month for the last 36 months (line chart)
  * alerts sent so far (single metric)
  * alerts in the next 48 hours (single metric)

## Task breakdown (as implemented)

| ID   | Task                                                | Location |
|------|-----------------------------------------------------|----------|
| T-01 | User model + registration endpoint                  | `backend/app/models/user.py`, `routers/auth.py` |
| T-02 | JWT + session table for multi-session support       | `services/security.py`, `models/session.py` |
| T-03 | Admin bootstrap on startup                          | `main.py::_bootstrap_admin` |
| T-04 | Medicine CRUD                                       | `routers/medicines.py` |
| T-05 | Alert materialization                               | `services/alerts.py::compute_alert_times` |
| T-06 | Scheduler tick (30 s)                               | `services/alerts.py::scheduler_tick` |
| T-07 | WebSocket alert channel                             | `routers/alerts.py::alerts_ws` |
| T-08 | Feedback endpoint                                   | `routers/feedback.py` |
| T-09 | Admin dashboard aggregates                          | `routers/admin.py` |
| T-10 | React SSR shell + runtime config injection          | `frontend/server/index.js` |
| T-11 | React pages (login/register/home/new/history/admin) | `frontend/client/src/pages/*` |
| T-12 | Recharts pie / bar / line for admin dashboard       | `frontend/client/src/pages/AdminDashboard.jsx` |
| T-13 | Synthetic data seeder                               | `backend/app/seed.py` |
| T-14 | Dual-mode config (local env vs Secret Manager)      | `backend/app/config.py` |
| T-15 | Dockerfiles + docker-compose                        | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` |
| T-16 | Cloud Build + Cloud Run manifests                   | `deploy/*` |
