import json
import logging
from pathlib import Path
from app.database import get_db_connection
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data"

def seed_database():
    """Seed sample doctors and demo patients if tables are empty."""
    conn = get_db_connection()
    try:
        # Check doctors
        doc_count = conn.execute("SELECT COUNT(*) as cnt FROM doctors").fetchone()["cnt"]
        if doc_count == 0:
            doctors_file = DATA_DIR / "sample_doctors.json"
            if doctors_file.exists():
                with open(doctors_file, "r", encoding="utf-8") as f:
                    doctors = json.load(f)
                for d in doctors:
                    conn.execute("""
                        INSERT INTO doctors (
                            name, specialization, qualification, facility_name, facility_type,
                            address, village_or_town, district, state, latitude, longitude,
                            phone, emergency_phone, operating_hours, consultation_fee,
                            languages_spoken, is_emergency_capable, is_teleconsult_available, rating
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        d["name"], d["specialization"], d.get("qualification", ""),
                        d["facility_name"], d["facility_type"], d["address"],
                        d.get("village_or_town", ""), d["district"], d["state"],
                        d["latitude"], d["longitude"], d["phone"],
                        d.get("emergency_phone", ""), d.get("operating_hours", ""),
                        d.get("consultation_fee", "Free"), d.get("languages_spoken", ""),
                        d.get("is_emergency_capable", 0), d.get("is_teleconsult_available", 0),
                        d.get("rating", 4.5)
                    ))
                conn.commit()
                logger.info(f"Seeded {len(doctors)} doctors and health centers into database.")

        # Check patients
        patient_count = conn.execute("SELECT COUNT(*) as cnt FROM patients").fetchone()["cnt"]
        if patient_count == 0:
            patients_file = DATA_DIR / "sample_patients.json"
            if patients_file.exists():
                with open(patients_file, "r", encoding="utf-8") as f:
                    patients = json.load(f)
                for p in patients:
                    conn.execute("""
                        INSERT INTO patients (
                            name, age, gender, village, district, state, phone, password_hash,
                            blood_group, allergies, chronic_conditions, preferred_language
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        p["name"], p["age"], p["gender"], p.get("village", ""),
                        p["district"], p["state"], p["phone"], hash_password(p["password"]),
                        p.get("blood_group", ""), p.get("allergies", ""),
                        p.get("chronic_conditions", ""), p.get("preferred_language", "en")
                    ))
                conn.commit()
                logger.info(f"Seeded {len(patients)} demo patients into database.")

        # Seed sample assessments if none exist so History screen has initial records for demo
        assess_count = conn.execute("SELECT COUNT(*) as cnt FROM assessments").fetchone()["cnt"]
        if assess_count == 0:
            conn.execute("""
                INSERT INTO assessments (
                    patient_id, patient_name, age, gender, location, primary_symptoms,
                    followup_answers, risk_level, is_emergency_rule, rule_triggered,
                    ai_summary, potential_causes, suggested_specialist, home_care_precautions,
                    when_to_seek_care, language
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1, "Basavaraju M.", 48, "Male", "Kailancha, Ramanagara", "Mild dry cough and throat irritation for 2 days",
                json.dumps({"cough_type": "Dry throat irritation", "cough_breathing": "No breathing issue"}),
                "Low Risk", 0, None,
                "Early upper respiratory tract irritation. Low risk. Supportive warm fluids and rest recommended.",
                json.dumps(["Common cold", "Mild viral pharyngitis", "Dust allergy"]),
                "General Physician",
                json.dumps(["Drink warm water and herbal tea", "Warm salt water gargle twice daily", "Avoid cold drinks"]),
                "If fever starts or symptoms persist beyond 4 days", "en"
            ))
            conn.execute("""
                INSERT INTO assessments (
                    patient_id, patient_name, age, gender, location, primary_symptoms,
                    followup_answers, risk_level, is_emergency_rule, rule_triggered,
                    ai_summary, potential_causes, suggested_specialist, home_care_precautions,
                    when_to_seek_care, language
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1, "Basavaraju M.", 48, "Male", "Kailancha, Ramanagara", "High fever with severe chills and body aches",
                json.dumps({"fever_duration": "3 to 5 days", "fever_severity": "Severe shivering / intense headache"}),
                "Moderate Risk", 0, None,
                "Persistent high fever with chills. Needs laboratory evaluation at PHC for seasonal infections.",
                json.dumps(["Viral fever / Flu", "Suspected Dengue or Malaria", "Bacterial infection"]),
                "General Physician / Internal Medicine",
                json.dumps(["Maintain strict hydration with ORS and tender coconut water", "Cold water forehead sponging", "Do not take unprescribed antibiotics"]),
                "Visit Kailancha PHC or Taluk Hospital within 24 hours for blood tests (CBC, smear)", "en"
            ))
            conn.commit()
            logger.info("Seeded initial medical history records for demo.")
    finally:
        conn.close()
