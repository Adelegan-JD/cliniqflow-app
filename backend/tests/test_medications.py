def test_only_pharmacy_or_admin_can_dispense(client, auth_headers_nurse):
    response = client.post(
        "/medications/order-items/not-an-item/dispenses",
        headers=auth_headers_nurse,
        json={"quantity": 10, "unit": "tablets"},
    )
    assert response.status_code == 403


def test_only_nurse_or_admin_can_administer(client, auth_headers_doctor):
    response = client.post(
        "/medications/order-items/not-an-item/administrations",
        headers=auth_headers_doctor,
        json={"status": "given", "dose_quantity": 5, "dose_unit": "mL"},
    )
    assert response.status_code == 403


def test_non_administration_status_requires_reason(client, auth_headers_nurse):
    response = client.post(
        "/medications/order-items/not-an-item/administrations",
        headers=auth_headers_nurse,
        json={"status": "held"},
    )
    assert response.status_code == 422
