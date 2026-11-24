import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

def test_homepage_serves_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "RuralCare AI" in resp.text
    assert "Symptom Checker" in resp.text

def test_auth_flow():
    # Login with demo patient
    login_resp = client.post("/api/auth/login", json={
        "phone": "9876543210",
        "password": "password123"
    })
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    token = data["access_token"]
    assert data["patient"]["name"] == "Basavaraju M."

    # Fetch /api/auth/me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["phone"] == "9876543210"

def test_triage_emergency_route():
    resp = client.post("/api/triage/assess", json={
        "symptoms": "Severe crushing chest pain radiating to left arm and sweating",
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_emergency"] is True
    assert data["risk_level"] == "Emergency Risk"
    assert "108" in data["emergency_action"]

def test_triage_non_emergency_and_followup():
    # Initial assessment
    assess_resp = client.post("/api/triage/assess", json={
        "symptoms": "Fever and mild body pain",
        "language": "en"
    })
    assert assess_resp.status_code == 200
    assess_data = assess_resp.json()
    assert assess_data["is_emergency"] is False
    assert len(assess_data["followup_questions"]) > 0

    # Follow-up assessment
    followup_resp = client.post("/api/triage/followup", json={
        "initial_symptoms": "Fever and mild body pain",
        "answers": {
            "fever_duration": "Less than 2 days",
            "fever_severity": "Mild chills / body ache"
        },
        "language": "en"
    })
    assert followup_resp.status_code == 200
    followup_data = followup_resp.json()
    assert followup_data["risk_level"] in ["Low Risk", "Moderate Risk"]
    assert len(followup_data["precautions"]) > 0
    assert followup_data["assessment_id"] is not None

def test_doctors_routes():
    # Districts
    dist_resp = client.get("/api/doctors/districts")
    assert dist_resp.status_code == 200
    assert "Ramanagara" in dist_resp.json()

    # Specializations
    spec_resp = client.get("/api/doctors/specializations")
    assert spec_resp.status_code == 200
    assert len(spec_resp.json()) > 0

    # Nearby doctors with coords
    docs_resp = client.get("/api/doctors/nearby?lat=12.7209&lon=77.2799")
    assert docs_resp.status_code == 200
    docs = docs_resp.json()
    assert len(docs) > 0
    assert docs[0]["distance_km"] is not None

def test_emergency_routes():
    # Helplines
    h_resp = client.get("/api/emergency/helplines")
    assert h_resp.status_code == 200
    assert h_resp.json()["emergency_numbers"]["ambulance"] == "108"

    # First aid guides
    fa_resp = client.get("/api/emergency/first-aid")
    assert fa_resp.status_code == 200
    assert len(fa_resp.json()) >= 4

    # SOS trigger
    sos_resp = client.post("/api/emergency/sos", json={
        "trigger_reason": "Test SOS trigger",
        "location": "Test Village, Ramanagara"
    })
    assert sos_resp.status_code == 200
    assert sos_resp.json()["status"] == "EMERGENCY_DISPATCHED"

def test_patient_history():
    resp = client.get("/api/triage/history")
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) > 0

if __name__ == "__main__":
    print("Testing API endpoints...")
    test_health_check()
    test_homepage_serves_html()
    test_auth_flow()
    test_triage_emergency_route()
    test_triage_non_emergency_and_followup()
    test_doctors_routes()
    test_emergency_routes()
    test_patient_history()
    print("All 8 API endpoint test suites PASSED!")
