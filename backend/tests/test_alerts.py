from datetime import datetime, timedelta, timezone

from tests.conftest import register_and_login


def test_medicine_creation_generates_upcoming_alerts(client):
    h = register_and_login(client)
    client.post(
        "/api/medicines",
        json={"name": "Med", "dosage": 100, "medicine_type": "Pill",
              "interval_hours": 6, "start_time": "0000"},
        headers=h,
    )
    upcoming = client.get("/api/alerts/upcoming", headers=h)
    assert upcoming.status_code == 200
    assert len(upcoming.json()) > 0


def test_due_alert_becomes_sent_and_can_be_acked(client):
    h = register_and_login(client)
    # Start time in the past today => at least one dose is already due.
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%H%M")
    client.post(
        "/api/medicines",
        json={"name": "DueMed", "dosage": 0, "medicine_type": "None",
              "interval_hours": 24, "start_time": past},
        headers=h,
    )
    due = client.get("/api/alerts/due", headers=h)
    assert due.status_code == 200
    assert len(due.json()) >= 1
    alert_id = due.json()[0]["id"]
    ack = client.post(f"/api/alerts/{alert_id}/ack", json={"action": "taken"}, headers=h)
    assert ack.status_code == 200 and ack.json()["status"] == "taken"
    # No longer surfaced as due.
    assert all(a["id"] != alert_id for a in client.get("/api/alerts/due", headers=h).json())


def test_history_shows_outcome(client):
    h = register_and_login(client)
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%H%M")
    client.post(
        "/api/medicines",
        json={"name": "HistMed", "dosage": 0, "medicine_type": "None",
              "interval_hours": 24, "start_time": past},
        headers=h,
    )
    # Fire the due alert (pending -> sent) then acknowledge as taken.
    aid = client.get("/api/alerts/due", headers=h).json()[0]["id"]
    client.post(f"/api/alerts/{aid}/ack", json={"action": "taken"}, headers=h)
    hist = client.get("/api/alerts/history", headers=h)
    assert hist.status_code == 200
    row = next(a for a in hist.json() if a["id"] == aid)
    assert row["status"] == "taken"
    assert row["sent_at"] is not None  # notified timestamp captured


def test_invalid_ack_action_rejected(client):
    h = register_and_login(client)
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%H%M")
    client.post(
        "/api/medicines",
        json={"name": "M2", "dosage": 0, "medicine_type": "None",
              "interval_hours": 24, "start_time": past},
        headers=h,
    )
    aid = client.get("/api/alerts/due", headers=h).json()[0]["id"]
    r = client.post(f"/api/alerts/{aid}/ack", json={"action": "nope"}, headers=h)
    assert r.status_code == 422
