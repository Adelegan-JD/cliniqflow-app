from unittest.mock import patch


def test_nlp_vitals_urgency_proxies(client, auth_headers_nurse):
    canned = {
        "urgency_level": "normal",
        "method": "rule_based",
        "rationale": "ok",
    }
    with patch(
        "app.services.ai_engine_client.post_json",
        return_value=canned,
    ) as m:
        r = client.post(
            "/nlp/vitals-urgency",
            headers=auth_headers_nurse,
            json={
                "patient_sex": "male",
                "bp_systolic": 120,
                "bp_diastolic": 80,
                "respiratory_rate": 20,
            },
        )
    assert r.status_code == 200
    assert r.json()["urgency_level"] == "normal"
    m.assert_called_once()


def test_ai_dose_check_proxies(client, auth_headers_doctor):
    canned = {
        "safe": True,
        "warnings": [],
        "recommended_range_mg_per_day": {"min": 0, "max": 100},
        "max_mg_per_day": 100,
        "event_id": "e1",
        "allow_override": True,
    }
    with patch(
        "app.services.ai_engine_client.post_json",
        return_value=canned,
    ):
        r = client.post(
            "/ai/dose-check",
            headers=auth_headers_doctor,
            json={
                "drug": "paracetamol",
                "age_years": 5,
                "weight_kg": 20,
                "frequency_per_day": 3,
                "chosen_dose_mg_per_day": 90,
            },
        )
    assert r.status_code == 200
    assert r.json()["safe"] is True
