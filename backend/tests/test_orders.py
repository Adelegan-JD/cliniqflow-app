def test_doctor_can_create_orders_but_nurse_cannot(client, auth_headers_doctor, auth_headers_nurse):
    payload = {
        "patient_id": "not-a-patient",
        "visit_id": "not-a-visit",
        "order_type": "laboratory",
        "items": [{"name": "Full blood count"}],
    }
    doctor_response = client.post("/orders", headers=auth_headers_doctor, json=payload)
    assert doctor_response.status_code == 404

    nurse_response = client.post("/orders", headers=auth_headers_nurse, json=payload)
    assert nurse_response.status_code == 403


def test_order_requires_encounter(client, auth_headers_doctor):
    response = client.post(
        "/orders",
        headers=auth_headers_doctor,
        json={"patient_id": "some-patient", "order_type": "imaging", "items": [{"name": "Chest X-ray"}]},
    )
    assert response.status_code == 422
