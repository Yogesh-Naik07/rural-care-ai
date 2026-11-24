import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "ruralcare.db"))

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "ruralcare-ai-super-secret-key-hackathon-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Gemini AI configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Emergency Helplines (India National & Rural Focus)
EMERGENCY_NUMBERS = {
    "ambulance": "108",
    "national_emergency": "112",
    "health_helpline": "104",      # 24x7 Medical Advice & Teleconsultation
    "women_helpline": "181",
    "child_helpline": "1098",
    "poison_control": "1800-116-117"
}

# Supported Languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "kn": "ಕನ್ನಡ (Kannada)",
    "hi": "हिन्दी (Hindi)",
    "ta": "தமிழ் (Tamil)",
    "te": "తెలుగు (Telugu)"
}
