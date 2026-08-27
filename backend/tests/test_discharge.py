def test_nurse_cannot_author_discharge_summary(client, auth_headers_nurse):
    response = client.put(
        "/discharge-summaries/admission/not-an-admission",
        headers=auth_headers_nurse,
        json={"discharge_diagnosis": "Improved", "hospital_course": "Observed overnight"},
    )
    assert response.status_code == 403


def test_doctor_can_only_save_summary_for_real_admission(client, auth_headers_doctor):
    response = client.put(
        "/discharge-summaries/admission/not-an-admission",
        headers=auth_headers_doctor,
        json={"discharge_diagnosis": "Improved", "hospital_course": "Observed overnight"},
    )
    assert response.status_code == 409
