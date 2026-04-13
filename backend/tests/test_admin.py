def test_admin_users_requires_auth(client):
    r = client.get("/admin/users")
    assert r.status_code == 401


def test_admin_users_ok(client, auth_headers_admin):
    r = client.get("/admin/users", headers=auth_headers_admin)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_admin_stats(client, auth_headers_admin):
    r = client.get("/admin/stats", headers=auth_headers_admin)
    assert r.status_code == 200
    data = r.json()
    assert "totalPatients" in data
