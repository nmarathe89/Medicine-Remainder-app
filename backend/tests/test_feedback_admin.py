from tests.conftest import make_admin, register_and_login


def test_submit_and_list_feedback(client):
    h = register_and_login(client)
    r = client.post("/api/feedback", json={"sentiment": "positive", "message": "nice"}, headers=h)
    assert r.status_code == 201
    lst = client.get("/api/feedback", headers=h)
    assert lst.status_code == 200 and len(lst.json()) == 1


def test_invalid_sentiment_rejected(client):
    h = register_and_login(client)
    r = client.post("/api/feedback", json={"sentiment": "meh"}, headers=h)
    assert r.status_code == 422


def test_admin_stats_require_admin(client):
    h = register_and_login(client)
    assert client.get("/api/admin/stats/users", headers=h).status_code == 403


def test_admin_user_stats(client):
    admin = make_admin(client)
    register_and_login(client, "u_a", "pass1234")
    register_and_login(client, "u_b", "pass1234")
    r = client.get("/api/admin/stats/users", headers=admin)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == body["active"] + body["inactive"]
    assert body["total"] >= 3


def test_admin_feedback_stats(client):
    admin = make_admin(client)
    h = register_and_login(client, "fbuser", "pass1234")
    client.post("/api/feedback", json={"sentiment": "positive"}, headers=h)
    client.post("/api/feedback", json={"sentiment": "negative"}, headers=h)
    r = client.get("/api/admin/stats/feedback", headers=admin)
    assert r.json() == {"positive": 1, "negative": 1}


def test_admin_user_trend_36_buckets(client):
    admin = make_admin(client)
    r = client.get("/api/admin/stats/user-trend", headers=admin)
    assert r.status_code == 200
    assert len(r.json()) == 37  # 3 years inclusive of current month boundary


def test_admin_alert_stats(client):
    admin = make_admin(client)
    r = client.get("/api/admin/stats/alerts", headers=admin)
    assert r.status_code == 200
    assert "total_sent" in r.json() and "upcoming_48h" in r.json()


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["status"] == "ok"
