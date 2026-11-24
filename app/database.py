import sqlite3
import json
import logging
from contextlib import contextmanager
from app.config import DATABASE_PATH

logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def db_session():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

def init_db():
    """Create all required tables if they don't already exist."""
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                village TEXT,
                district TEXT NOT NULL,
                state TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                blood_group TEXT,
                allergies TEXT,
                chronic_conditions TEXT,
                preferred_language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Assessments / Medical History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                patient_name TEXT,
                age INTEGER,
                gender TEXT,
                location TEXT,
                primary_symptoms TEXT NOT NULL,
                followup_answers TEXT,
                risk_level TEXT NOT NULL,
                is_emergency_rule INTEGER DEFAULT 0,
                rule_triggered TEXT,
                ai_summary TEXT,
                potential_causes TEXT,
                suggested_specialist TEXT,
                home_care_precautions TEXT,
                when_to_seek_care TEXT,
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL
            )
        """)

        # Doctors & Healthcare Facilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                qualification TEXT,
                facility_name TEXT NOT NULL,
                facility_type TEXT NOT NULL,
                address TEXT NOT NULL,
                village_or_town TEXT,
                district TEXT NOT NULL,
                state TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                phone TEXT NOT NULL,
                emergency_phone TEXT,
                operating_hours TEXT,
                consultation_fee TEXT,
                languages_spoken TEXT,
                is_emergency_capable INTEGER DEFAULT 0,
                is_teleconsult_available INTEGER DEFAULT 0,
                rating REAL DEFAULT 4.5
            )
        """)

        # Emergency alerts log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emergency_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                patient_name TEXT,
                phone TEXT,
                location TEXT,
                latitude REAL,
                longitude REAL,
                trigger_reason TEXT NOT NULL,
                status TEXT DEFAULT 'initiated',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Database initialized successfully.")
