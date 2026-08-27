def test_billing_requires_auth(client):
    response = client.get("/billing/invoices")
    assert response.status_code == 401


def test_doctor_cannot_access_billing(client, auth_headers_doctor):
    response = client.get("/billing/invoices", headers=auth_headers_doctor)
    assert response.status_code == 403


def test_billing_officer_cannot_confirm_payments(client, auth_headers_billing_officer):
    response = client.post("/billing/payments/not-a-payment/confirm", headers=auth_headers_billing_officer)
    assert response.status_code == 403
