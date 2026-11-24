from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.database import get_db_connection
from app.models import DoctorResponse
from app.services.doctor_service import get_doctors, get_doctor_by_id

router = APIRouter(prefix="/api/doctors", tags=["Doctor & Hospital Finder"])

@router.get("/nearby", response_model=List[DoctorResponse])
def find_nearby_doctors(
    lat: Optional[float] = Query(None, description="User latitude"),
    lon: Optional[float] = Query(None, description="User longitude"),
    district: Optional[str] = Query(None, description="Filter by district"),
    specialization: Optional[str] = Query(None, description="Filter by doctor specialization"),
    facility_type: Optional[str] = Query(None, description="Filter by facility type (PHC, CHC, Hospital)"),
    emergency_only: bool = Query(False, description="Filter only emergency capable centers"),
    max_distance_km: float = Query(100.0, description="Max search radius in km")
):
    """Search doctors and hospitals with optional GPS distance computation and filters."""
    doctors = get_doctors(
        user_lat=lat,
        user_lon=lon,
        district=district,
        specialization=specialization,
        facility_type=facility_type,
        emergency_only=emergency_only,
        max_distance_km=max_distance_km
    )
    return doctors

@router.get("/districts", response_model=List[str])
def list_districts():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT DISTINCT district FROM doctors ORDER BY district ASC").fetchall()
        return [r["district"] for r in rows if r["district"]]
    finally:
        conn.close()

@router.get("/specializations", response_model=List[str])
def list_specializations():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT DISTINCT specialization FROM doctors ORDER BY specialization ASC").fetchall()
        return [r["specialization"] for r in rows if r["specialization"]]
    finally:
        conn.close()

@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor_detail(doctor_id: int):
    doc = get_doctor_by_id(doctor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor or facility not found")
    return doc
