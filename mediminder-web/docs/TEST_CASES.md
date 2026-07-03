# Test Cases

Backend tests live under `backend/tests/` and are executed by pytest.
They cover every task in `USE_CASES.md`. Frontend is validated by manual
browsing against the running stack (see `docs/TEST_RESULTS.md`).

| TC ID | Task | File | Test | What it proves |
|-------|------|------|------|----------------|
| TC-01 | T-01 | `test_auth.py` | `test_register_and_login` | UC-01 + UC-02 happy path. |
| TC-02 | T-01 | `test_auth.py` | `test_register_duplicate_username_rejected` | UC-01 alt flow (409). |
| TC-03 | T-01 | `test_auth.py` | `test_login_wrong_password` | UC-02 alt flow (401). |
| TC-04 | T-03 | `test_auth.py` | `test_admin_login` | UC-03 happy path. |
| TC-05 | T-03 | `test_auth.py` | `test_non_admin_cannot_admin_login` | UC-03 privilege check (403). |
| TC-06 | T-04 | `test_medicines.py` | `test_create_and_list_medicine` | UC-05 happy path. |
| TC-07 | T-04 | `test_medicines.py` | `test_duplicate_medicine_rejected` | UC-05 duplicate rule. |
| TC-08 | T-04 | `test_medicines.py` | `test_invalid_interval_rejected` | UC-05 validation on interval. |
| TC-09 | T-04 | `test_medicines.py` | `test_invalid_start_time_rejected` | UC-05 validation on start-time format. |
| TC-10 | T-04 | `test_medicines.py` | `test_delete_medicine` | UC-06. |
| TC-11 | T-02 | `test_medicines.py` | `test_unauth_access_denied` | JWT required, 401 otherwise. |
| TC-12 | T-05 | `test_alerts_and_admin.py` | `test_alerts_materialized_on_medicine_create` | UC-07 pre-materialization. |
| TC-13 | T-08 | `test_alerts_and_admin.py` | `test_feedback_roundtrip` | UC-09. |
| TC-14 | T-09 | `test_alerts_and_admin.py` | `test_admin_dashboard_shape` | UC-10 payload shape and metrics. |
| TC-15 | T-09 | `test_alerts_and_admin.py` | `test_admin_only` | UC-10 privilege check (403). |
| TC-16 |  —   | `test_alerts_and_admin.py` | `test_health` | `/api/health` liveness. |

Every test uses the same in-memory SQLite fixture (see `tests/conftest.py`),
so the whole suite runs in about 1.5 seconds on a modest laptop and needs
no docker to execute.
