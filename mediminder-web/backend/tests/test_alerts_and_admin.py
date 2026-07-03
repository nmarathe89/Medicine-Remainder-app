"""TC-10..TC-14: alert scheduling, feedback, admin dashboard aggregates."""

from __future__ import annotations

import pytest


async def _register_and_login(client, username, is_admin=False):
    await client.post("/api/auth/register", json={
        "username": username, "email": f"{username}@example.com", "password": "secret1",
    })
    r = await client.post("/api/auth/login", json={"username": username, "password": "secret1"})
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_alerts_materialized_on_medicine_create(client):
    tok = await _register_and_login(client, "jack")
    hdrs = {"Authorization": f"Bearer {tok}"}
    await client.post("/api/medicines", headers=hdrs, json={
        "name": "Metformin", "dosage_mg": 500,
        "medicine_type": "Pill", "interval_hours": 8, "start_time": "0800",
    })
    r = await client.get("/api/alerts", headers=hdrs)
    assert r.status_code == 200
    # 3 slots/day * 3 days lookback in the compute (48h horizon) => >= 3.
    assert len(r.json()) >= 3


@pytest.mark.asyncio
async def test_alerts_respect_medicine_timezone(client):
    """start_time is a wall-clock in the medicine's timezone, not UTC.

    A 6-hour interval starting at 08:00 Asia/Kolkata should place slots at
    08:00, 14:00, 20:00, 02:00 IST — i.e. 02:30, 08:30, 14:30, 20:30 UTC.
    Regression test for the bug where the code stored `start_time` as UTC.
    """
    from datetime import datetime
    tok = await _register_and_login(client, "nikhil")
    hdrs = {"Authorization": f"Bearer {tok}"}
    r = await client.post("/api/medicines", headers=hdrs, json={
        "name": "Crocin", "dosage_mg": 500,
        "medicine_type": "Tablet", "interval_hours": 6, "start_time": "0800",
        "timezone": "Asia/Kolkata",
    })
    assert r.status_code == 201, r.text
    r = await client.get("/api/alerts", headers=hdrs)
    assert r.status_code == 200
    # Every scheduled_at, taken modulo 24h, must be one of the four IST slots
    # converted to UTC minutes-of-day.
    ist_minutes = {8*60, 14*60, 20*60, 2*60}       # local
    utc_minutes = {(m - 330) % (24*60) for m in ist_minutes}
    for a in r.json():
        dt = datetime.fromisoformat(a["scheduled_at"].replace("Z", "+00:00"))
        m = dt.hour * 60 + dt.minute
        assert m in utc_minutes, f"scheduled_at {a['scheduled_at']} not on an IST slot"


@pytest.mark.asyncio
async def test_feedback_roundtrip(client):
    tok = await _register_and_login(client, "kate")
    hdrs = {"Authorization": f"Bearer {tok}"}
    r = await client.post("/api/feedback", headers=hdrs, json={
        "sentiment": "positive", "message": "Great app!",
    })
    assert r.status_code == 201
    r = await client.get("/api/feedback/mine", headers=hdrs)
    assert len(r.json()) == 1
    assert r.json()[0]["sentiment"] == "positive"


@pytest.mark.asyncio
async def test_admin_dashboard_shape(client):
    # regular user (bumps total_users)
    await _register_and_login(client, "leo")
    # admin
    r = await client.post("/api/auth/admin/login", json={"username": "admin", "password": "admin123"})
    admin_tok = r.json()["access_token"]
    hdrs = {"Authorization": f"Bearer {admin_tok}"}
    r = await client.get("/api/admin/dashboard", headers=hdrs)
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) >= {"users", "feedback_last_year", "user_trend_3y", "alerts"}
    assert body["users"]["total"] >= 2  # admin + leo
    assert "sent_total" in body["alerts"]
    assert "upcoming_48h" in body["alerts"]


@pytest.mark.asyncio
async def test_admin_only(client):
    tok = await _register_and_login(client, "mallory")
    r = await client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
