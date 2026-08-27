def test_clinical_form_template_requires_admin(client, auth_headers_doctor):
    response = client.post(
        "/clinical-forms/templates",
        headers=auth_headers_doctor,
        json={
            "code": "EYE-EXAM",
            "name": "Ophthalmology Examination",
            "schema_json": {"fields": [{"key": "visual_acuity", "label": "Visual acuity", "type": "text"}]},
        },
    )
    assert response.status_code == 403


def test_admin_can_create_specialty_template(client, auth_headers_admin):
    response = client.post(
        "/clinical-forms/templates",
        headers=auth_headers_admin,
        json={
            "code": "PAEDS-REVIEW",
            "name": "Paediatric Review",
            "schema_json": {"fields": [{"key": "weight_kg", "label": "Weight", "type": "number"}]},
        },
    )
    assert response.status_code == 201
    assert response.json()["version"] == 1
