def test_nurse_stats_requires_auth(client):
    r = client.get("/nurse/stats")
    assert r.status_code == 401


def test_nurse_stats_ok(client, auth_headers_nurse):
    r = client.get("/nurse/stats", headers=auth_headers_nurse)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "totalPatientsToday" in data
    assert "awaitingTriage" in data
    assert "awaitingConsultation" in data
    assert "visitsEnded" in data


def test_nurse_triage_queue_requires_auth(client):
    r = client.get("/nurse/triage-queue")
    assert r.status_code == 401


def test_nurse_triage_queue_ok(client, auth_headers_nurse):
    r = client.get("/nurse/triage-queue", headers=auth_headers_nurse)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    for item in body:
        assert item["status"] == "awaiting_triage"
        assert "patientId" in item
        assert "name" in item
        assert "age" in item
        assert "sex" in item
