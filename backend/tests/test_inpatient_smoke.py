def test_inpatient_admission_to_discharge_smoke(
    client, auth_headers_admin, auth_headers_doctor, auth_headers_nurse, auth_headers_record_officer
):
    patient_response = client.post(
        "/record-officer/register-patient",
        headers=auth_headers_record_officer,
        json={
            "firstName": "Test", "lastName": "Inpatient", "dob": "2018-01-01", "gender": "Male",
            "phone": "08030000000", "address": "Test address", "nokName": "Test Guardian",
            "nokRelationship": "Parent", "nokPhone": "08030000001",
        },
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    admission_response = client.post(
        "/hospital/admissions",
        headers=auth_headers_doctor,
        json={"patient_id": patient_id, "admission_type": "emergency", "admission_reason": "Observation required"},
    )
    assert admission_response.status_code == 201
    admission_id = admission_response.json()["id"]

    observation_response = client.post(
        f"/hospital/admissions/{admission_id}/observations",
        headers=auth_headers_nurse,
        json={"temperature_c": 37.2, "oxygen_saturation": 98, "notes": "Stable on arrival"},
    )
    assert observation_response.status_code == 201

    summary_response = client.put(
        f"/discharge-summaries/admission/{admission_id}",
        headers=auth_headers_doctor,
        json={"discharge_diagnosis": "Improved", "hospital_course": "Observed and remained stable", "finalize": True},
    )
    assert summary_response.status_code == 200
    assert summary_response.json()["status"] == "final"

    discharge_response = client.post(
        f"/hospital/admissions/{admission_id}/discharge",
        headers=auth_headers_doctor,
        json={"discharge_disposition": "Home"},
    )
    assert discharge_response.status_code == 200
    assert discharge_response.json()["status"] == "discharged"
