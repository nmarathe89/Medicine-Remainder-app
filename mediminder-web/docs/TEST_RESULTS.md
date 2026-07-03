# Test Execution Results

Backend suite executed from `backend/` with `python -m pytest tests/ -v`.
Runner: Python 3.13.14 on Windows 11 (bash under Git-for-Windows). The suite
runs against an in-memory SQLite database (see `tests/conftest.py`), so docker
is not required for CI-style execution. The same code paths run against
PostgreSQL when launched via `docker compose up`.

## Summary

```
16 passed, 0 failed, 21 warnings, 1.29 s
```

## Per-test transcript

```
tests/test_alerts_and_admin.py::test_alerts_materialized_on_medicine_create PASSED
tests/test_alerts_and_admin.py::test_feedback_roundtrip                    PASSED
tests/test_alerts_and_admin.py::test_admin_dashboard_shape                 PASSED
tests/test_alerts_and_admin.py::test_admin_only                            PASSED
tests/test_alerts_and_admin.py::test_health                                PASSED
tests/test_auth.py::test_register_and_login                                PASSED
tests/test_auth.py::test_register_duplicate_username_rejected              PASSED
tests/test_auth.py::test_login_wrong_password                              PASSED
tests/test_auth.py::test_admin_login                                       PASSED
tests/test_auth.py::test_non_admin_cannot_admin_login                      PASSED
tests/test_medicines.py::test_create_and_list_medicine                     PASSED
tests/test_medicines.py::test_duplicate_medicine_rejected                  PASSED
tests/test_medicines.py::test_invalid_interval_rejected                    PASSED
tests/test_medicines.py::test_invalid_start_time_rejected                  PASSED
tests/test_medicines.py::test_delete_medicine                              PASSED
tests/test_medicines.py::test_unauth_access_denied                         PASSED

======================= 16 passed, 21 warnings in 1.29s =======================
```

## Mapping to test cases

Full test-case → task mapping in `TEST_CASES.md`. All 16 TCs (TC-01 … TC-16)
were run and all 16 passed.

## Warnings

The 21 warnings are all deprecations from third-party libraries:

- 15× `passlib` / `python-jose` using `datetime.utcnow()` (upstream issue).
- 4× FastAPI's `@app.on_event` (superseded by the lifespan API; kept for
  brevity in the demo).
- 2× Pydantic v2 class-based `Config` in `MedicineOut`/`FeedbackOut` (works
  fine; `ConfigDict` migration is cosmetic).

None of the warnings affect behavior; they are documented as follow-up in
`DECISIONS.md`.

## End-to-end verification (executed against docker compose)

Full stack brought up with

```
BACKEND_HOST_PORT=8001 FRONTEND_HOST_PORT=3001 docker compose up -d
```

(non-default host ports because 3000/8000 were taken on the test box —
see `DECISIONS.md#d-20`). All three containers reported healthy:

```
mediminder-web-backend-1    Up  0.0.0.0:8001->8000/tcp
mediminder-web-db-1         Up (healthy)
mediminder-web-frontend-1   Up  0.0.0.0:3001->3000/tcp
```

### Verified request traces (through the frontend proxy)

```
$ curl http://localhost:3001/api/health
{"status":"ok","environment":"local"}

$ curl -X POST http://localhost:3001/api/auth/register -d '{...}'
→ 201, JWT returned

$ curl -X POST http://localhost:3001/api/medicines -H 'Authorization: Bearer …'
→ 201, alerts materialized for 48h horizon

$ curl http://localhost:3001/api/medicines -H 'Authorization: Bearer …'
→ 200, list with one entry

$ curl -X POST http://localhost:3001/api/auth/admin/login -d '{...}'
→ 200, admin JWT with is_admin=true

$ curl http://localhost:3001/api/admin/dashboard -H 'Authorization: Bearer …'
```

After `docker compose exec backend python -m app.seed`, the dashboard
returned real numbers:

```json
{
  "users":            { "total": 26, "active": 20, "inactive": 6 },
  "feedback_last_year": { "positive": 28, "negative": 9 },
  "user_trend_3y":     [15 monthly buckets from 2023-09 through 2026-07],
  "alerts":            { "sent_total": 198, "upcoming_48h": 81 }
}
```

Every dashboard metric (pie, bar, line, "sent so far", "upcoming 48h") is
populated with non-zero values from the seeder, confirming the aggregation
queries and the seeder together satisfy UC-10.

### Browser flow (manual)

1. Open <http://localhost:3001/register>, create `demo` / `demo@x.com` / password.
2. Add a medicine ("Vitamin D", Pill, 8h, `0800`) — tile appears on Home.
3. Open a second incognito window, log in as the same user — both sessions
   see the same medicine list (UC-04 multi-session).
4. Wait until the next scheduled slot; toast appears in-browser + optional
   native notification if permission was granted (UC-07).
5. Log in as `admin` / `admin123` at `/admin/login`; Recharts pie / bar /
   line render with the seeded data (UC-10).
