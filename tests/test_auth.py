from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token
from app.database import get_db_connection

def test_password_hashing():
    pw = "ruralcareSecure123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert "$" in hashed
    assert verify_password(pw, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_token():
    payload = {"sub": "42", "name": "Ramesh"}
    token = create_access_token(payload)
    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "42"
    assert decoded["name"] == "Ramesh"

def test_demo_patient_exists():
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM patients WHERE phone = '9876543210'").fetchone()
        assert row is not None
        assert row["name"] == "Basavaraju M."
        assert verify_password("password123", row["password_hash"]) is True
    finally:
        conn.close()
