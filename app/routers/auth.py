from fastapi import APIRouter, HTTPException, Depends, status
from app.database import get_db_connection
from app.models import PatientRegisterRequest, PatientLoginRequest, PatientResponse, TokenResponse
from app.services.auth_service import hash_password, verify_password, create_access_token, get_current_patient_required, get_current_patient_optional

router = APIRouter(prefix="/api/auth", tags=["Authentication & Patient"])

@router.post("/register", response_model=TokenResponse)
def register_patient(payload: PatientRegisterRequest):
    conn = get_db_connection()
    try:
        # Check if phone number is already registered
        existing = conn.execute("SELECT id FROM patients WHERE phone = ?", (payload.phone,)).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A patient with this mobile number is already registered. Please log in."
            )

        hashed_pw = hash_password(payload.password)
        cursor = conn.execute("""
            INSERT INTO patients (
                name, age, gender, village, district, state, phone, password_hash,
                blood_group, allergies, chronic_conditions, preferred_language
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payload.name, payload.age, payload.gender, payload.village,
            payload.district, payload.state, payload.phone, hashed_pw,
            payload.blood_group, payload.allergies, payload.chronic_conditions,
            payload.preferred_language or 'en'
        ))
        conn.commit()
        patient_id = cursor.lastrowid

        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        patient_dict = dict(row)
        del patient_dict["password_hash"]

        token = create_access_token({"sub": str(patient_id), "name": payload.name, "phone": payload.phone})

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            patient=PatientResponse(**patient_dict)
        )
    finally:
        conn.close()

@router.post("/login", response_model=TokenResponse)
def login_patient(payload: PatientLoginRequest):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM patients WHERE phone = ?", (payload.phone,)).fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mobile number not found. Please register first."
            )
        patient_dict = dict(row)
        if not verify_password(payload.password, patient_dict["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password. Please verify and try again."
            )

        del patient_dict["password_hash"]
        token = create_access_token({"sub": str(patient_dict["id"]), "name": patient_dict["name"], "phone": patient_dict["phone"]})

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            patient=PatientResponse(**patient_dict)
        )
    finally:
        conn.close()

@router.get("/me", response_model=PatientResponse)
def get_profile(patient: dict = Depends(get_current_patient_required)):
    patient_dict = patient.copy()
    if "password_hash" in patient_dict:
        del patient_dict["password_hash"]
    return PatientResponse(**patient_dict)
