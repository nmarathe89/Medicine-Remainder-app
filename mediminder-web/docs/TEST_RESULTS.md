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

## Frontend verification (manual)

Because the frontend is a browser app that depends on user interaction, it
is verified manually against the running docker-compose stack:

1. `docker compose up --build` and wait until backend `/api/health` returns 200.
2. Browse to <http://localhost:3000/register>, create `demo`.
3. Add "Vitamin D", Pill, 8h, `0800`. Verify tile shows on Home.
4. Open a second incognito window, log in as the same user — both sessions
   see the same medicine list (validates UC-04 multi-session).
5. Wait 30 s past a scheduled alert time; toast appears in-browser
   (validates UC-07). If browser notification permission was granted, a
   native notification also fires.
6. Log out, log in as `admin` / `admin123` at `/admin/login`. Dashboard
   loads pie / bar / line charts (validates UC-10).
7. `docker compose exec backend python -m app.seed` to populate history
   and see all four aggregate metrics with non-zero values.

Steps 1-7 were performed against the compose stack at development time and
match the assertions in the automated suite (which validates the same shapes
and status codes at the API level).
