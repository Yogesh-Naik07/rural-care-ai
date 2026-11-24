from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Authentication & Patient Models ---

class PatientRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=0, le=125)
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    village: Optional[str] = ""
    district: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=4)
    blood_group: Optional[str] = ""
    allergies: Optional[str] = ""
    chronic_conditions: Optional[str] = ""
    preferred_language: Optional[str] = "en"

class PatientLoginRequest(BaseModel):
    phone: str
    password: str

class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    village: Optional[str] = ""
    district: str
    state: str
    phone: str
    blood_group: Optional[str] = ""
    allergies: Optional[str] = ""
    chronic_conditions: Optional[str] = ""
    preferred_language: str = "en"
    created_at: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    patient: PatientResponse


# --- Symptom Checker & Triage Models ---

class FollowupQuestion(BaseModel):
    id: str
    question_text: str
    question_text_local: Optional[str] = ""
    input_type: str = "select"  # "select" or "boolean" or "text"
    options: List[str] = []

class TriageInitialRequest(BaseModel):
    symptoms: str = Field(..., min_length=2)
    language: str = "en"
    patient_id: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None

class TriageFollowupRequest(BaseModel):
    initial_symptoms: str
    answers: Dict[str, str] = {}
    language: str = "en"
    patient_id: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None

class TriageResponse(BaseModel):
    risk_level: str  # "Emergency Risk", "Moderate Risk", "Low Risk"
    is_emergency: bool = False
    emergency_action: Optional[str] = None
    rule_triggered: Optional[str] = None
    summary: str
    possible_causes: List[str] = []
    suggested_specialist: str = "General Physician"
    precautions: List[str] = []
    when_to_seek_care: str
    followup_questions: List[FollowupQuestion] = []
    assessment_id: Optional[int] = None
    disclaimer: str = (
        "RuralCare AI is an assistive healthcare screening tool, not a medical diagnosis. "
        "In case of severe symptoms, visit a healthcare center or call 108 immediately."
    )


class AssessmentRecord(BaseModel):
    id: int
    patient_id: Optional[int]
    patient_name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    location: Optional[str]
    primary_symptoms: str
    followup_answers: Optional[Dict[str, Any]] = None
    risk_level: str
    is_emergency_rule: bool
    rule_triggered: Optional[str]
    ai_summary: Optional[str]
    potential_causes: Optional[List[str]] = None
    suggested_specialist: Optional[str]
    home_care_precautions: Optional[List[str]] = None
    when_to_seek_care: Optional[str]
    language: str
    created_at: str


# --- Doctor Finder Models ---

class DoctorQueryRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    specialization: Optional[str] = None
    facility_type: Optional[str] = None
    emergency_only: Optional[bool] = False
    max_distance_km: Optional[float] = 50.0

class DoctorResponse(BaseModel):
    id: int
    name: str
    specialization: str
    qualification: Optional[str] = ""
    facility_name: str
    facility_type: str
    address: str
    village_or_town: Optional[str] = ""
    district: str
    state: str
    latitude: float
    longitude: float
    phone: str
    emergency_phone: Optional[str] = ""
    operating_hours: Optional[str] = ""
    consultation_fee: Optional[str] = "Free at Govt PHC"
    languages_spoken: Optional[str] = "English, Kannada, Hindi"
    is_emergency_capable: bool = False
    is_teleconsult_available: bool = False
    rating: float = 4.5
    distance_km: Optional[float] = None


# --- Emergency & SOS Models ---

class EmergencyAlertRequest(BaseModel):
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    trigger_reason: str = "Manual SOS Trigger"
