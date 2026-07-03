# Features → Use Cases → Tasks

Derived from the original Flutter app plus the new web/multi-user/admin
requirements.

## Feature 1 — Account & Authentication (new)
**UC-1.1 Register** — A visitor creates an account with username + password.
- T-1.1.1 Validate username (≥3) and password (≥4).
- T-1.1.2 Reject duplicate usernames.
- T-1.1.3 Store bcrypt password hash.

**UC-1.2 User login** — A user authenticates and receives a session token.
- T-1.2.1 Verify credentials; issue JWT + create session row.
- T-1.2.2 Reject bad credentials / inactive accounts.

**UC-1.3 Admin login** — An admin authenticates to the admin area.
- T-1.3.1 Verify credentials AND role == admin.

**UC-1.4 Multi-session & logout** — A user may be logged in from several
browsers/tabs simultaneously.
- T-1.4.1 Each login creates an independent session row.
- T-1.4.2 List active sessions.
- T-1.4.3 Logout revokes a session.

## Feature 2 — Medicine management (ported)
**UC-2.1 Add medicine** — mirrors the original "Add New Mediminder".
- T-2.1.1 Require name; reject duplicate name for the same user.
- T-2.1.2 Validate interval ∈ {6,8,12,24} and start time (HHMM).
- T-2.1.3 Optional dosage + type (Bottle/Pill/Syringe/Tablet/None).
- T-2.1.4 On create, generate upcoming dose alerts.

**UC-2.2 List medicines** — show all of the user's medicines with doses/day.

**UC-2.3 View medicine detail** — fetch one medicine (owner-scoped).

**UC-2.4 Delete medicine** — remove medicine and cascade its alerts.

**UC-2.5 Data isolation** — a user can never see another user's medicines.

## Feature 3 — Reminders / browser alerts (re-platformed)
**UC-3.1 Generate schedule** — from start time + interval, create `24/interval`
dose times per day (ported from `scheduleNotification`).

**UC-3.2 Poll due alerts** — client polls; due pending alerts flip to `sent`
and are returned for display as browser toasts (no email/SMS).

**UC-3.3 Acknowledge alert** — user marks a reminder `taken` or `skipped`.

**UC-3.4 Upcoming alerts** — list pending alerts in the future.

## Feature 4 — Feedback (new, feeds admin analytics)
**UC-4.1 Submit feedback** — sentiment (positive/negative) + message.
**UC-4.2 List own feedback.**

## Feature 5 — Admin dashboard (new)
**UC-5.1 User stats** — total, active, inactive (→ pie chart).
**UC-5.2 Feedback stats** — positive/negative in last 12 months.
**UC-5.3 User trend** — monthly signups over the last 3 years.
**UC-5.4 Alert stats** — total alerts sent so far; upcoming in next 48h.
**UC-5.5 RBAC** — all admin endpoints require an admin token.

## Traceability summary
| Use case | API endpoint(s) | Tests |
|----------|-----------------|-------|
| UC-1.1 | `POST /api/auth/register` | test_auth |
| UC-1.2 | `POST /api/auth/login` | test_auth |
| UC-1.3 | `POST /api/auth/admin/login` | test_auth |
| UC-1.4 | `GET /api/auth/sessions`, `POST /api/auth/logout` | test_auth |
| UC-2.* | `/api/medicines` CRUD | test_medicines |
| UC-3.* | `/api/alerts/{due,upcoming,ack}` | test_alerts |
| UC-4.* | `/api/feedback` | test_feedback_admin |
| UC-5.* | `/api/admin/stats/*` | test_feedback_admin |
