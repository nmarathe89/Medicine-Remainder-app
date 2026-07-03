# Test Execution Results

Backend test suite executed **for real** during development.

- **Runner:** pytest 8.3.4
- **Python:** 3.13.14 (local dev; container target is `python:3.14-slim`)
- **Test DB:** in-memory SQLite (shared `StaticPool`) — the same application code runs against PostgreSQL in Docker Compose / Cloud.
- **Command:** `pytest` (run from `backend/`)
- **Outcome:** ✅ **23 passed** in ~11s

## Captured output

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.3.4, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: .../backend
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.1
collecting ... collected 23 items

tests/test_alerts.py::test_medicine_creation_generates_upcoming_alerts PASSED [  4%]
tests/test_alerts.py::test_due_alert_becomes_sent_and_can_be_acked PASSED [  8%]
tests/test_alerts.py::test_invalid_ack_action_rejected PASSED            [ 13%]
tests/test_auth.py::test_register_creates_user PASSED                    [ 17%]
tests/test_auth.py::test_register_duplicate_rejected PASSED              [ 21%]
tests/test_auth.py::test_login_success_and_bad_password PASSED           [ 26%]
tests/test_auth.py::test_admin_login_requires_admin_role PASSED          [ 30%]
tests/test_auth.py::test_multiple_sessions_supported PASSED              [ 34%]
tests/test_auth.py::test_protected_route_requires_token PASSED           [ 39%]
tests/test_feedback_admin.py::test_submit_and_list_feedback PASSED       [ 43%]
tests/test_feedback_admin.py::test_invalid_sentiment_rejected PASSED     [ 47%]
tests/test_feedback_admin.py::test_admin_stats_require_admin PASSED      [ 52%]
tests/test_feedback_admin.py::test_admin_user_stats PASSED               [ 56%]
tests/test_feedback_admin.py::test_admin_feedback_stats PASSED           [ 60%]
tests/test_feedback_admin.py::test_admin_user_trend_36_buckets PASSED    [ 65%]
tests/test_feedback_admin.py::test_admin_alert_stats PASSED              [ 69%]
tests/test_feedback_admin.py::test_healthz PASSED                        [ 73%]
tests/test_medicines.py::test_create_and_list_medicine PASSED            [ 78%]
tests/test_medicines.py::test_duplicate_name_rejected PASSED             [ 82%]
tests/test_medicines.py::test_invalid_interval_rejected PASSED           [ 86%]
tests/test_medicines.py::test_invalid_start_time_rejected PASSED         [ 91%]
tests/test_medicines.py::test_get_and_delete_medicine PASSED             [ 95%]
tests/test_medicines.py::test_user_isolation PASSED                      [100%]

============================= 23 passed in 10.87s =============================
```

## Coverage by task (see `test-cases.md` for the mapping)

| Area | Tests |
|------|-------|
| Registration / login / admin login / multi-session / auth guard | `test_auth.py` (6) |
| Medicine CRUD, validation, duplicate rule, user isolation | `test_medicines.py` (6) |
| Alert generation, due→sent transition, acknowledge, validation | `test_alerts.py` (3) |
| Feedback submit/list + validation | `test_feedback_admin.py` (2) |
| Admin analytics (users pie, feedback, 3-yr trend, alerts) + RBAC + health | `test_feedback_admin.py` (8) |

## Notes / issues found & fixed during the run
1. **Windows SQLite file lock** — switched the test DB from a temp file to in-memory SQLite with `StaticPool` (`app/database.py`, `tests/conftest.py`).
2. **Cross-backend datetime comparison** — SQLite returns naive datetimes, Postgres aware; normalized via `_naive()` in `app/alerts.py` so filtering works on both.
3. **Alert generation excluded already-elapsed doses today** — adjusted the generator to include today's elapsed doses (so they surface as "due") while never materializing pre-today doses.
