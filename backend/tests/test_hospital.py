def test_hospital_configuration_requires_auth(client):
    response = client.get("/hospital/departments")
    assert response.status_code == 401


def test_admin_can_create_department_and_doctor_can_view_it(client, auth_headers_admin, auth_headers_doctor):
    response = client.post(
        "/hospital/departments",
        headers=auth_headers_admin,
        json={"code": "TEST-PAEDS", "name": "Test Paediatrics", "specialty": "Paediatrics"},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["code"] == "TEST-PAEDS"

    response = client.get("/hospital/departments", headers=auth_headers_doctor)
    assert response.status_code == 200
    assert any(item["code"] == "TEST-PAEDS" for item in response.json())


def test_nurse_cannot_change_hospital_configuration(client, auth_headers_nurse):
    response = client.post(
        "/hospital/departments",
        headers=auth_headers_nurse,
        json={"code": "UNAUTH", "name": "Unauthorised Department"},
    )
    assert response.status_code == 403
