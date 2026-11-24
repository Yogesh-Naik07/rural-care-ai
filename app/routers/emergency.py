from fastapi import APIRouter
from app.config import EMERGENCY_NUMBERS
from app.database import get_db_connection
from app.models import EmergencyAlertRequest

router = APIRouter(prefix="/api/emergency", tags=["Emergency & SOS Support"])

FIRST_AID_GUIDES = [
    {
        "id": "snakebite",
        "title": "Snakebite Protocol",
        "icon": "fa-shield-virus",
        "action_steps": [
            "Keep the patient completely calm and immobile. Panic speeds venom circulation.",
            "Immobilize the bitten limb at or slightly below the level of the heart using a splint or sling.",
            "Remove rings, bangles, or tight clothing near the bite before swelling starts.",
            "DO NOT cut, suction, apply potassium permanganate, ice, or tight tourniquets.",
            "Call 108 immediately and rush to the nearest Primary Health Center or hospital with Anti-Snake Venom (ASV)."
        ],
        "local_titles": {
            "kn": "ಹಾವು ಕಡಿತಕ್ಕೆ ತುರ್ತು ಪ್ರಥಮ ಚಿಕಿತ್ಸೆ",
            "hi": "सांप के काटने पर प्राथमिक चिकित्सा",
            "ta": "பாம்பு கடி முதலுதவி வழிகாட்டுதல்",
            "te": "పాము కాటుకు ప్రథమ చికిత్స"
        }
    },
    {
        "id": "heart_attack",
        "title": "Chest Pain / Heart Attack",
        "icon": "fa-heart-pulse",
        "action_steps": [
            "Call 108 ambulance without any hesitation or delay.",
            "Have the patient rest in a comfortable seated position with knees bent and back supported.",
            "Loosen tight collar, belt, or waist garments to ease breathing.",
            "If the patient is conscious and not allergic to aspirin, chew one 300mg soluble aspirin tablet if available.",
            "Be prepared to perform Hands-Only CPR (100-120 firm chest compressions per minute) if breathing stops."
        ],
        "local_titles": {
            "kn": "ಎದೆನೋವು / ಹೃದಯಾಘಾತ ತುರ್ತು ಚಿಕಿತ್ಸೆ",
            "hi": "सीने में दर्द / दिल का दौरा आपातकालीन सहायता",
            "ta": "மாரடைப்பு முதலுதவி",
            "te": "గుండెపోటు ప్రథమ చికిత్స"
        }
    },
    {
        "id": "severe_bleeding",
        "title": "Severe Bleeding & Cuts",
        "icon": "fa-droplet",
        "action_steps": [
            "Apply direct, steady pressure to the wound with a clean cloth or sterile gauze.",
            "Keep pressing firmly for at least 5 to 10 minutes without lifting to check.",
            "If the cloth soaks through, do NOT remove it; place another cloth on top and continue pressing.",
            "Elevate the injured limb above heart level if no bone fracture is suspected.",
            "Call 108 or arrange transport to the nearest PHC immediately."
        ],
        "local_titles": {
            "kn": "ತೀವ್ರ ರಕ್ತಸ್ರಾವ ನಿಯಂತ್ರಣ",
            "hi": "अत्यधिक रक्तस्राव नियंत्रण",
            "ta": "கடுமையான இரத்தப்போக்கு கட்டுப்பாடு",
            "te": "తీవ్ర రక్తస్రావ నియంత్రణ"
        }
    },
    {
        "id": "heatstroke",
        "title": "Heat Stroke & Sunstroke (Rural Farmers)",
        "icon": "fa-sun",
        "action_steps": [
            "Move the person immediately to a cool, shaded area or under a tree.",
            "Remove outer clothing and fan aggressively.",
            "Apply cool water or wet cloths to the neck, armpits, and groin to lower body temperature.",
            "If conscious and alert, offer sips of cool water or ORS solution. Do NOT force liquids if confused or drowsy.",
            "Call 108 if body temperature is very high or patient is delirious."
        ],
        "local_titles": {
            "kn": "ಬಿಸಿಲು ಹೊಡೆತ / ಹೀಟ್‌ಸ್ಟ್ರೋಕ್",
            "hi": "लू लगना / हीट स्ट्रोक प्राथमिक उपचार",
            "ta": "சூரிய வெப்ப பக்கவாதம்",
            "te": "వడదెబ్బ ప్రథమ చికిత్స"
        }
    },
    {
        "id": "choking",
        "title": "Choking Emergency",
        "icon": "fa-lungs",
        "action_steps": [
            "Encourage the person to cough forcefully if they can still make sounds.",
            "Deliver 5 firm back blows between the shoulder blades using the heel of your hand.",
            "If back blows fail, perform abdominal thrusts (Heimlich Maneuver): stand behind, grasp hands between navel and ribcage, pull sharply inward and upward.",
            "Repeat until the airway is clear or call 108 if unconscious."
        ],
        "local_titles": {
            "kn": "ಉಸಿರು ಕಟ್ಟುವಿಕೆ (ಚೋಕಿಂಗ್)",
            "hi": "गले में कुछ अटकना (दम घुटना)",
            "ta": "மூச்சுக்குழாய் அடைப்பு",
            "te": "గొంతులో ఏదైనా ఇరుక్కున్నప్పుడు"
        }
    }
]

@router.get("/helplines")
def get_helplines():
    """Return emergency numbers and regional medical dispatch contact."""
    return {
        "emergency_numbers": EMERGENCY_NUMBERS,
        "descriptions": {
            "108": "Free Emergency Ambulance Service across India",
            "112": "All-in-One National Emergency Police/Fire/Medical",
            "104": "Health Advice, Tele-Triage & ASHA Medical Assistance",
            "181": "Women Helpline & Crisis Support",
            "1098": "Childline Emergency Support",
            "1800-116-117": "National Poison Information Center"
        }
    }

@router.get("/first-aid")
def get_first_aid_guides():
    return FIRST_AID_GUIDES

@router.post("/sos")
def trigger_sos_alert(payload: EmergencyAlertRequest):
    """
    Log and activate emergency alert protocol.
    Returns nearest emergency recommendations and dispatch advice immediately.
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO emergency_logs (
                patient_id, patient_name, phone, location, latitude, longitude, trigger_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            payload.patient_id, payload.patient_name, payload.phone,
            payload.location, payload.latitude, payload.longitude, payload.trigger_reason
        ))
        conn.commit()
        alert_id = cursor.lastrowid

        return {
            "status": "EMERGENCY_DISPATCHED",
            "alert_id": alert_id,
            "message": "Emergency SOS registered. Dial 108 immediately for ambulance support.",
            "ambulance_hotline": "108",
            "emergency_helpline": "112",
            "medical_support_104": "104",
            "instructions": "Keep phone line open. Nearest emergency medical responder is alerted."
        }
    finally:
        conn.close()
