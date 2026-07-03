from tests.conftest import make_admin, register_and_login


def test_register_creates_user(client):
    r = client.post("/api/auth/register", json={"username": "newuser", "password": "pass1234"})
    assert r.status_code == 201
    assert r.json()["username"] == "newuser"
    assert r.json()["role"] == "user"


def test_register_duplicate_rejected(client):
    client.post("/api/auth/register", json={"username": "dup", "password": "pass1234"})
    r = client.post("/api/auth/register", json={"username": "dup", "password": "pass1234"})
    assert r.status_code == 409


def test_login_success_and_bad_password(client):
    client.post("/api/auth/register", json={"username": "usr", "password": "pass1234"})
    ok = client.post("/api/auth/login", json={"username": "usr", "password": "pass1234"})
    assert ok.status_code == 200 and ok.json()["access_token"]
    bad = client.post("/api/auth/login", json={"username": "usr", "password": "wrong"})
    assert bad.status_code == 401


def test_admin_login_requires_admin_role(client):
    client.post("/api/auth/register", json={"username": "plain", "password": "pass1234"})
    r = client.post("/api/auth/admin/login", json={"username": "plain", "password": "pass1234"})
    assert r.status_code == 403
    headers = make_admin(client, "boss", "admin123")
    assert "Authorization" in headers


def test_multiple_sessions_supported(client):
    register_and_login(client, "multi", "pass1234")
    # Second login for the same user creates a second session token.
    h1 = register_and_login(client, "multi2", "pass1234")
    client.post("/api/auth/login", json={"username": "multi2", "password": "pass1234"})
    r = client.get("/api/auth/sessions", headers=h1)
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_protected_route_requires_token(client):
    r = client.get("/api/medicines")
    assert r.status_code == 401
