# Test Cases

Each case maps to a task in `use-cases.md`. Automated results are captured in
`TEST_RESULTS.md` (23 passing). Tests live in `backend/tests/`.

| ID | Task | Description | Input | Expected | Automated test | Result |
|----|------|-------------|-------|----------|----------------|--------|
| TC-01 | T-1.1.1/3 | Register valid user | `newuser/pass1234` | 201, role=user | `test_register_creates_user` | ✅ Pass |
| TC-02 | T-1.1.2 | Duplicate username rejected | register `dup` twice | 2nd → 409 | `test_register_duplicate_rejected` | ✅ Pass |
| TC-03 | T-1.2.1/2 | Login good & bad password | valid then wrong pw | 200 + token / 401 | `test_login_success_and_bad_password` | ✅ Pass |
| TC-04 | T-1.3.1 | Admin login requires admin role | non-admin then admin | 403 / 200 | `test_admin_login_requires_admin_role` | ✅ Pass |
| TC-05 | T-1.4.1/2 | Multiple sessions per user | login twice | ≥2 session rows | `test_multiple_sessions_supported` | ✅ Pass |
| TC-06 | T-2.* guard | Protected route needs token | no auth header | 401 | `test_protected_route_requires_token` | ✅ Pass |
| TC-07 | T-2.1.*/2.2 | Create + list medicine | valid medicine (8h) | 201, doses_per_day=3 | `test_create_and_list_medicine` | ✅ Pass |
| TC-08 | T-2.1.1 | Duplicate medicine name | same name twice | 409 | `test_duplicate_name_rejected` | ✅ Pass |
| TC-09 | T-2.1.2 | Invalid interval | interval=5 | 422 | `test_invalid_interval_rejected` | ✅ Pass |
| TC-10 | T-2.1.2 | Invalid start time | `2599` | 422 | `test_invalid_start_time_rejected` | ✅ Pass |
| TC-11 | T-2.3/2.4 | Get then delete medicine | create→get→delete→get | 200/204/404 | `test_get_and_delete_medicine` | ✅ Pass |
| TC-12 | T-2.5 | User data isolation | user B reads user A's med | 404 | `test_user_isolation` | ✅ Pass |
| TC-13 | T-3.1/3.4 | Creation generates upcoming alerts | new medicine | upcoming list non-empty | `test_medicine_creation_generates_upcoming_alerts` | ✅ Pass |
| TC-14 | T-3.2/3.3 | Due alert → sent → ack | start 1h ago | due≥1, ack=taken, then not due | `test_due_alert_becomes_sent_and_can_be_acked` | ✅ Pass |
| TC-15 | T-3.3 | Invalid ack action | action=`nope` | 422 | `test_invalid_ack_action_rejected` | ✅ Pass |
| TC-16 | T-4.1/4.2 | Submit + list feedback | positive/"nice" | 201, list len 1 | `test_submit_and_list_feedback` | ✅ Pass |
| TC-17 | T-4.1 | Invalid sentiment | `meh` | 422 | `test_invalid_sentiment_rejected` | ✅ Pass |
| TC-18 | T-5.5 | Admin stats require admin | user token | 403 | `test_admin_stats_require_admin` | ✅ Pass |
| TC-19 | UC-5.1 | User stats sum | 3 users | total = active+inactive | `test_admin_user_stats` | ✅ Pass |
| TC-20 | UC-5.2 | Feedback stats | 1 pos + 1 neg | {positive:1,negative:1} | `test_admin_feedback_stats` | ✅ Pass |
| TC-21 | UC-5.3 | User trend buckets | — | 37 monthly points (3 yrs) | `test_admin_user_trend_36_buckets` | ✅ Pass |
| TC-22 | UC-5.4 | Alert stats shape | — | has total_sent + upcoming_48h | `test_admin_alert_stats` | ✅ Pass |
| TC-23 | infra | Health check | `GET /healthz` | 200, status ok | `test_healthz` | ✅ Pass |

## Manual / UI test checklist (via `docker compose up`)
- [ ] Register → redirected to login; login → dashboard loads.
- [ ] Add medicine with start time a few minutes ago → toast appears within ~15s.
- [ ] Click **Taken** / **Skip** → toast dismisses and does not reappear.
- [ ] Submit feedback → confirmation shown.
- [ ] Admin login (`admin/admin123`) → dashboard renders pie, bar, and 3-year line charts populated from seed data.
- [ ] Open two browsers, log in as the same user → both work (multi-session).
