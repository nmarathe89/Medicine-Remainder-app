from tests.conftest import register_and_login


def _valid_medicine(**over):
    m = {
        "name": "Paracetamol",
        "dosage": 500,
        "medicine_type": "Tablet",
        "interval_hours": 8,
        "start_time": "0800",
    }
    m.update(over)
    return m


def test_create_and_list_medicine(client):
    h = register_and_login(client)
    r = client.post("/api/medicines", json=_valid_medicine(), headers=h)
    assert r.status_code == 201
    assert r.json()["doses_per_day"] == 3  # 24 / 8
    lst = client.get("/api/medicines", headers=h)
    assert lst.status_code == 200 and len(lst.json()) == 1


def test_duplicate_name_rejected(client):
    h = register_and_login(client)
    client.post("/api/medicines", json=_valid_medicine(), headers=h)
    dup = client.post("/api/medicines", json=_valid_medicine(), headers=h)
    assert dup.status_code == 409


def test_invalid_interval_rejected(client):
    h = register_and_login(client)
    r = client.post("/api/medicines", json=_valid_medicine(interval_hours=5), headers=h)
    assert r.status_code == 422


def test_invalid_start_time_rejected(client):
    h = register_and_login(client)
    r = client.post("/api/medicines", json=_valid_medicine(start_time="2599"), headers=h)
    assert r.status_code == 422


def test_get_and_delete_medicine(client):
    h = register_and_login(client)
    created = client.post("/api/medicines", json=_valid_medicine(), headers=h).json()
    mid = created["id"]
    assert client.get(f"/api/medicines/{mid}", headers=h).status_code == 200
    assert client.delete(f"/api/medicines/{mid}", headers=h).status_code == 204
    assert client.get(f"/api/medicines/{mid}", headers=h).status_code == 404


def test_user_isolation(client):
    h1 = register_and_login(client, "owner", "pass1234")
    mid = client.post("/api/medicines", json=_valid_medicine(), headers=h1).json()["id"]
    h2 = register_and_login(client, "intruder", "pass1234")
    assert client.get(f"/api/medicines/{mid}", headers=h2).status_code == 404
