"""TC-05..TC-09: medicine CRUD and validation."""

from __future__ import annotations

import pytest


async def _token(client, username="eve", password="secret1"):
    await client.post("/api/auth/register", json={
        "username": username, "email": f"{username}@example.com", "password": password,
    })
    r = await client.post("/api/auth/login", json={"username": username, "password": password})
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_create_and_list_medicine(client):
    tok = await _token(client)
    hdrs = {"Authorization": f"Bearer {tok}"}
    r = await client.post("/api/medicines", headers=hdrs, json={
        "name": "Paracetamol", "dosage_mg": 500,
        "medicine_type": "Pill", "interval_hours": 8, "start_time": "0800",
    })
    assert r.status_code == 201, r.text
    r = await client.get("/api/medicines", headers=hdrs)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["name"] == "Paracetamol"


@pytest.mark.asyncio
async def test_duplicate_medicine_rejected(client):
    tok = await _token(client, "frank")
    hdrs = {"Authorization": f"Bearer {tok}"}
    body = {
        "name": "Aspirin", "dosage_mg": 100,
        "medicine_type": "Tablet", "interval_hours": 12, "start_time": "0900",
    }
    await client.post("/api/medicines", headers=hdrs, json=body)
    r = await client.post("/api/medicines", headers=hdrs, json=body)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_invalid_interval_rejected(client):
    tok = await _token(client, "grace")
    hdrs = {"Authorization": f"Bearer {tok}"}
    r = await client.post("/api/medicines", headers=hdrs, json={
        "name": "Weird", "dosage_mg": 10,
        "medicine_type": "Pill", "interval_hours": 5, "start_time": "0800",
    })
    assert r.status_code == 422  # 5 isn't in {6,8,12,24}


@pytest.mark.asyncio
async def test_invalid_start_time_rejected(client):
    tok = await _token(client, "hank")
    hdrs = {"Authorization": f"Bearer {tok}"}
    r = await client.post("/api/medicines", headers=hdrs, json={
        "name": "BadTime", "dosage_mg": 10,
        "medicine_type": "Pill", "interval_hours": 8, "start_time": "8am",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_delete_medicine(client):
    tok = await _token(client, "irene")
    hdrs = {"Authorization": f"Bearer {tok}"}
    r = await client.post("/api/medicines", headers=hdrs, json={
        "name": "Vitamin D", "dosage_mg": 25,
        "medicine_type": "Tablet", "interval_hours": 24, "start_time": "0800",
    })
    med_id = r.json()["id"]
    r = await client.delete(f"/api/medicines/{med_id}", headers=hdrs)
    assert r.status_code == 204
    r = await client.get("/api/medicines", headers=hdrs)
    assert r.json() == []


@pytest.mark.asyncio
async def test_unauth_access_denied(client):
    r = await client.get("/api/medicines")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_delete_cancels_future_alerts_but_keeps_history(client):
    """Deleting a medicine should:
      * remove its FUTURE pending alerts (no zombie notifications)
      * leave PAST alerts alone (audit trail intact)
      * flag remaining rows on /api/alerts as medicine_deleted=true.
    """
    from datetime import datetime, timedelta, timezone
    from app.database import SessionLocal
    from app.models import Alert

    tok = await _token(client, "jules")
    hdrs = {"Authorization": f"Bearer {tok}"}
    r = await client.post("/api/medicines", headers=hdrs, json={
        "name": "Aspirin-history", "dosage_mg": 100,
        "medicine_type": "Tablet", "interval_hours": 12, "start_time": "0800",
    })
    med_id = r.json()["id"]

    # Manually insert one past + one future alert so we can assert the split.
    now = datetime.now(tz=timezone.utc)
    async with SessionLocal() as db:
        # Look up the user id from the token by fetching /api/medicines.
        rows = await db.execute(__import__("sqlalchemy").select(Alert).where(Alert.medicine_id == med_id))
        user_id = rows.scalars().first().user_id
        db.add(Alert(user_id=user_id, medicine_id=med_id,
                     scheduled_at=now - timedelta(hours=2), sent_at=now - timedelta(hours=2),
                     status="sent"))
        db.add(Alert(user_id=user_id, medicine_id=med_id,
                     scheduled_at=now + timedelta(hours=48), status="pending"))
        await db.commit()

    r = await client.delete(f"/api/medicines/{med_id}", headers=hdrs)
    assert r.status_code == 204

    r = await client.get("/api/alerts?limit=100", headers=hdrs)
    assert r.status_code == 200
    body = r.json()
    # Past 'sent' row must survive; every remaining row must be flagged.
    assert any(a["status"] == "sent" for a in body), "past history was lost"
    assert all(a["medicine_deleted"] for a in body), "medicine_deleted flag not set"
    # No pending future alerts should remain — they were purged on delete.
    future = [a for a in body if a["status"] == "pending"]
    assert future == [], f"expected 0 future pending alerts, got {len(future)}"
