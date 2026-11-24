import math
import json
import logging
from typing import List, Optional
from app.database import get_db_connection
from app.models import DoctorResponse

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def get_doctors(
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    district: Optional[str] = None,
    specialization: Optional[str] = None,
    facility_type: Optional[str] = None,
    emergency_only: bool = False,
    max_distance_km: float = 100.0
) -> List[DoctorResponse]:
    """Retrieve and filter doctors and facilities, computing distance if coordinates provided."""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM doctors WHERE 1=1"
        params = []

        if district and district.strip().lower() != "all":
            query += " AND LOWER(district) = LOWER(?)"
            params.append(district.strip())

        if specialization and specialization.strip().lower() != "all":
            query += " AND LOWER(specialization) LIKE LOWER(?)"
            params.append(f"%{specialization.strip()}%")

        if facility_type and facility_type.strip().lower() != "all":
            query += " AND LOWER(facility_type) LIKE LOWER(?)"
            params.append(f"%{facility_type.strip()}%")

        if emergency_only:
            query += " AND is_emergency_capable = 1"

        rows = conn.execute(query, params).fetchall()
        results: List[DoctorResponse] = []

        for row in rows:
            doc_data = dict(row)
            doc_data["is_emergency_capable"] = bool(doc_data.get("is_emergency_capable", 0))
            doc_data["is_teleconsult_available"] = bool(doc_data.get("is_teleconsult_available", 0))

            dist = None
            if user_lat is not None and user_lon is not None:
                dist = haversine_distance(user_lat, user_lon, doc_data["latitude"], doc_data["longitude"])
                if dist > max_distance_km:
                    continue  # Filter out doctors outside radius

            doc_data["distance_km"] = dist
            results.append(DoctorResponse(**doc_data))

        # Sort by distance if user coords available, else by rating
        if user_lat is not None and user_lon is not None:
            results.sort(key=lambda d: (d.distance_km if d.distance_km is not None else float("inf")))
        else:
            results.sort(key=lambda d: d.rating, reverse=True)

        return results
    finally:
        conn.close()

def get_doctor_by_id(doctor_id: int) -> Optional[DoctorResponse]:
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["is_emergency_capable"] = bool(data.get("is_emergency_capable", 0))
        data["is_teleconsult_available"] = bool(data.get("is_teleconsult_available", 0))
        return DoctorResponse(**data)
    finally:
        conn.close()
