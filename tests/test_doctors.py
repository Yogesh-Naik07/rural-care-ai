from app.services.doctor_service import haversine_distance, get_doctors

def test_haversine_distance():
    # Distance between Ramanagara (12.7209, 77.2799) and Channapatna (12.6518, 77.2089) ~ 10-12 km
    dist = haversine_distance(12.7209, 77.2799, 12.6518, 77.2089)
    assert 10.0 <= dist <= 12.0

def test_get_doctors_all():
    docs = get_doctors()
    assert len(docs) >= 5

def test_get_doctors_district_filter():
    docs = get_doctors(district="Ramanagara")
    assert len(docs) > 0
    for d in docs:
        assert d.district.lower() == "ramanagara"

def test_get_doctors_emergency_capable():
    docs = get_doctors(emergency_only=True)
    assert len(docs) > 0
    for d in docs:
        assert d.is_emergency_capable is True

def test_get_doctors_distance_sorting():
    # User in Ramanagara center
    docs = get_doctors(user_lat=12.7209, user_lon=77.2799)
    assert len(docs) > 0
    # First doctor should be closest (< 5 km)
    assert docs[0].distance_km is not None
    assert docs[0].distance_km < 5.0
