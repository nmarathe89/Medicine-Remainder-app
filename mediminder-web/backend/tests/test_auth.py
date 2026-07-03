"""TC-01..TC-04: registration, login, admin login, duplicate handling."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    r = await client.post("/api/auth/register", json={
        "username": "alice", "email": "alice@example.com", "password": "wonderland",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["username"] == "alice"
    assert body["is_admin"] is False
    assert body["access_token"]

    r = await client.post("/api/auth/login", json={"username": "alice", "password": "wonderland"})
    assert r.status_code == 200
    assert r.json()["access_token"]


@pytest.mark.asyncio
async def test_register_duplicate_username_rejected(client):
    await client.post("/api/auth/register", json={
        "username": "bob", "email": "bob@example.com", "password": "secret1",
    })
    r = await client.post("/api/auth/register", json={
        "username": "bob", "email": "bob2@example.com", "password": "secret2",
    })
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "username": "carol", "email": "c@example.com", "password": "rightpass",
    })
    r = await client.post("/api/auth/login", json={"username": "carol", "password": "wrongpass"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_login(client):
    r = await client.post("/api/auth/admin/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    assert r.json()["is_admin"] is True


@pytest.mark.asyncio
async def test_non_admin_cannot_admin_login(client):
    await client.post("/api/auth/register", json={
        "username": "dave", "email": "d@example.com", "password": "secret1",
    })
    r = await client.post("/api/auth/admin/login", json={"username": "dave", "password": "secret1"})
    assert r.status_code == 403
