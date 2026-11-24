import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.models import FollowupQuestion

logger = logging.getLogger(__name__)

# Heuristic clinical symptom profiles for robust offline triage & follow-up questions
SYMPTOM_PROFILES = {
    "fever": {
        "keywords": ["fever", "temperature", "chills", "bukhar", "kaayikalu", "juram", "jvara", "ಜ್ವರ", "बुखार", "காய்ச்சல்", "జ్వరం"],
        "followups": [
            {
                "id": "fever_duration",
                "question_text": "How many days have you had the fever?",
                "question_text_local": {
                    "kn": "ಜ್ವರ ಬಂದು ಎಷ್ಟು ದಿನಗಳಾಗಿವೆ?",
                    "hi": "बुखार कितने दिनों से है?",
                    "ta": "காய்ச்சல் எத்தனை நாட்களாக உள்ளது?",
                    "te": "జ్వరం వచ్చి ఎన్ని రోజులైంది?"
                },
                "options": ["Less than 2 days", "3 to 5 days", "More than 5 days", "More than 2 weeks"]
            },
            {
                "id": "fever_severity",
                "question_text": "Are you experiencing severe chills, shivering, or body pain?",
                "question_text_local": {
                    "kn": "ತೀವ್ರ ಚಳಿ, ನಡುಕ ಅಥವಾ ಮೈಕೈ ನೋವು ಇದೆಯೇ?",
                    "hi": "क्या तेज ठंड, कंपकंपी या शरीर में दर्द महसूस हो रहा है?",
                    "ta": "கடும் குளிர், நடுக்கம் அல்லது உடல் வலி உள்ளதா?",
                    "te": "తీవ్రమైన చలి, వణుకు లేదా ఒళ్లు నొప్పులు ఉన్నాయా?"
                },
                "options": ["Mild chills / body ache", "Severe shivering / intense headache", "None"]
            },
            {
                "id": "fever_redflags",
                "question_text": "Do you notice any red spots/rash on skin, or bleeding from nose/gums?",
                "question_text_local": {
                    "kn": "ಚರ್ಮದ ಮೇಲೆ ಕೆಂಪು ಕಲೆಗಳು ಅಥವಾ ಮೂಗಿನಿಂದ ರಕ್ತಸ್ರಾವವಿದೆಯೇ?",
                    "hi": "क्या त्वचा पर लाल चकत्ते या नाक/मसूड़ों से खून आ रहा है?",
                    "ta": "தோலில் சிவப்பு புள்ளிகள் அல்லது மூக்கிலிருந்து ரத்தம் வருகிறதா?",
                    "te": "చర్మంపై ఎర్రటి మచ్చలు లేదా ముక్కు/చిగుళ్ళ నుండి రక్తం కారుతోందా?"
                },
                "options": ["No such signs", "Yes, skin rash / red spots", "Yes, minor bleeding"]
            }
        ],
        "specialist": "General Physician / Internal Medicine",
        "causes": ["Viral fever", "Seasonal influenza", "Dengue / Malaria (if accompanied by chills & rash)", "Bacterial infection"],
        "precautions": [
            "Drink plenty of clean boiled water, tender coconut water, or ORS to stay hydrated.",
            "Rest adequately in a well-ventilated room.",
            "Apply cool wet cloth compresses on the forehead to gently lower temperature.",
            "Do NOT take self-prescribed antibiotics or heavy painkillers without a doctor's consultation."
        ]
    },
    "cough_cold": {
        "keywords": ["cough", "cold", "sore throat", "runny nose", "khasi", "sardi", "kemmu", "irogolu", "kasi", "daggulu", "ಕೆಮ್ಮು", "ನೆಗಡಿ", "खांसी", "जुकाम", "இருமல்", "சளி", "దగ్గు", "జలుబు"],
        "followups": [
            {
                "id": "cough_type",
                "question_text": "Is the cough dry or producing colored phlegm (yellow/green/brown)?",
                "question_text_local": {
                    "kn": "ಕೆಮ್ಮು ಒಣ ಕೆಮ್ಮೇ ಅಥವಾ ಕಫ (ಹಳದಿ/ಹಸಿರು) ಬರುತ್ತಿದೆಯೇ?",
                    "hi": "क्या खांसी सूखी है या कफ (पीला/हरा) आ रहा है?",
                    "ta": "இருமல் வறட்டு இருமலா அல்லது சளி வெளிவருகிறதா?",
                    "te": "దగ్గు పొడి దగ్గా లేదా కఫం వస్తోందా?"
                },
                "options": ["Dry throat irritation", "White/clear phlegm", "Thick yellow or green phlegm", "Blood in phlegm"]
            },
            {
                "id": "cough_breathing",
                "question_text": "Are you feeling any chest heaviness or slight wheezing when lying down?",
                "question_text_local": {
                    "kn": "ಮಲಗಿದಾಗ ಎದೆಯಲ್ಲಿ ಶಬ್ದ ಅಥವಾ ಉಸಿರಾಟದಲ್ಲಿ ಭಾರವಾಗುತ್ತಿದೆಯೇ?",
                    "hi": "क्या लेटने पर सीने में भारीपन या सांस में घरघराहट हो रही है?",
                    "ta": "படுக்கும்போது நெஞ்சு பாரமாக அல்லது மூச்சிரைப்பு உள்ளதா?",
                    "te": "పడుకున్నప్పుడు ఛాతీ బరువుగా లేదా శ్వాసలో పిల్లికూతలు వస్తున్నాయా?"
                },
                "options": ["No breathing issue", "Mild wheezing/stiffness", "Significant difficulty breathing"]
            }
        ],
        "specialist": "General Physician / Pulmonologist",
        "causes": ["Upper respiratory tract infection (Common Cold)", "Allergic bronchitis", "Pharyngitis / Tonsillitis", "Seasonal flu"],
        "precautions": [
            "Inhale warm steam 2-3 times daily for soothing nasal passage.",
            "Gargle with warm salt water for throat relief.",
            "Drink warm water, tulsi/ginger tea, or warm soups.",
            "Avoid cold drinks, ice, and dusty environments."
        ]
    },
    "stomach_pain": {
        "keywords": ["stomach", "abdominal", "belly", "loose motions", "diarrhea", "vomiting", "pet dard", "hota noovu", "vayiru vali", "kadupu noppi", "ಹೊಟ್ಟೆ ನೋವು", "ಭೇದಿ", "पेट दर्द", "दस्त", "வயிறு வலி", "வயிற்றுப்போக்கு", "కడుపు నొప్పి", "విరేచనాలు"],
        "followups": [
            {
                "id": "stomach_location",
                "question_text": "Where is the pain predominantly felt?",
                "question_text_local": {
                    "kn": "ನೋವು ಮುಖ್ಯವಾಗಿ ಹೊಟ್ಟೆಯ ಯಾವ ಭಾಗದಲ್ಲಿದೆ?",
                    "hi": "दर्द मुख्य रूप से पेट के किस हिस्से में है?",
                    "ta": "வலி முக்கியமாக வயிற்றின் எந்த பகுதியில் உள்ளது?",
                    "te": "నొప్పి ప్రధానంగా కడుపులో ఏ భాగంలో ఉంది?"
                },
                "options": ["Upper stomach (burning / acidity)", "Lower right abdomen (sharp pain)", "All over stomach / cramps", "Lower abdomen with burning urine"]
            },
            {
                "id": "stomach_loose_motions",
                "question_text": "Do you have watery loose motions or repeated vomiting?",
                "question_text_local": {
                    "kn": "ನಿರಂತರ ಭೇದಿ ಅಥವಾ ಪದೇ ಪದೇ ವಾಂತಿಯಾಗುತ್ತಿದೆಯೇ?",
                    "hi": "क्या बार-बार पतले दस्त या उल्टी हो रही है?",
                    "ta": "தொடர் வயிற்றுப்போக்கு அல்லது வாந்தி உள்ளதா?",
                    "te": "పదే పదే నీళ్ల విరేచనాలు లేదా వాంతులు అవుతున్నాయా?"
                },
                "options": ["None", "1 to 3 times", "More than 5 times (feeling weak/dizzy)"]
            }
        ],
        "specialist": "General Physician / Gastroenterologist",
        "causes": ["Acute gastroenteritis / Food poisoning", "Gastritis / Acid reflux", "Indigestion", "Intestinal amoebiasis"],
        "precautions": [
            "Start Oral Rehydration Salts (ORS) solution immediately: 1 packet in 1 liter clean boiled-cooled water.",
            "Drink rice kanji / tender coconut water / diluted buttermilk.",
            "Eat light, soft food like khichdi, curd rice, or bananas.",
            "Avoid spicy, oily, fried foods, and raw roadside food."
        ]
    },
    "headache_fatigue": {
        "keywords": ["headache", "head pain", "migraine", "dizzy", "dizziness", "tired", "sar dard", "thale noovu", "thalai vali", "thala noppi", "ತಲೆ ನೋವು", "ತಲೆಸುತ್ತು", "सिर दर्द", "चक्कर", "தலைவலி", "மயக்கம்", "తలనొప్పి", "తలతిరగడం"],
        "followups": [
            {
                "id": "headache_severity",
                "question_text": "How severe is the headache?",
                "question_text_local": {
                    "kn": "ತಲೆನೋವಿನ ತೀವ್ರತೆ ಎಷ್ಟಿದೆ?",
                    "hi": "सिरदर्द कितना तेज है?",
                    "ta": "தலைவலி எவ்வளவு தீவிரமாக உள்ளது?",
                    "te": "తలనొప్పి ఎంత తీవ్రంగా ఉంది?"
                },
                "options": ["Mild / dull pressure", "Moderate throbbing on one side", "Sudden explosive / worst pain of life"]
            },
            {
                "id": "headache_vision",
                "question_text": "Are you experiencing blurred vision, neck stiffness, or dizziness when standing up?",
                "question_text_local": {
                    "kn": "ಕಣ್ಣು ಮಸುಕಾಗುವುದು, ಕುತ್ತಿಗೆ ಬಿಗಿಯುವುದು ಅಥವಾ ಎದ್ದು ನಿಂತಾಗ ತಲೆಸುತ್ತುವುದು ಇದೆಯೇ?",
                    "hi": "क्या नजर धुंधली हो रही है, गर्दन में अकड़न है, या खड़े होने पर चक्कर आ रहे हैं?",
                    "ta": "பார்வை மங்குதல், கழுத்து விறைப்பு அல்லது நிற்கும்போது தலைச்சுற்றல் உள்ளதா?",
                    "te": "కంటి చూపు మసకబారడం, మెడ పట్టేయడం లేదా నిలబడినప్పుడు తల తిరగడం ఉందా?"
                },
                "options": ["No other symptoms", "Dizziness / fatigue", "Neck stiffness with high fever"]
            }
        ],
        "specialist": "General Physician / Neurologist",
        "causes": ["Tension headache / Fatigue", "Dehydration / Heat exhaustion", "Migraine", "Sinus pressure"],
        "precautions": [
            "Drink at least 2 to 3 glasses of clean water immediately.",
            "Rest in a quiet, darkened, cool room.",
            "Avoid skipping meals and ensure adequate sleep.",
            "Limit exposure to bright mobile screens and direct hot sun."
        ]
    },
    "joint_bone_pain": {
        "keywords": ["joint", "knee", "back pain", "arthritis", "bone", "swelling", "sandhi noovu", "kamardard", "moottu vali", "keelu noppi", "ಕೀಲು ನೋವು", "ಸೊಂಟ ನೋವು", "जोड़ों का दर्द", "कमर दर्द", "மூட்டு வலி", "కీళ్ల నొప్పులు"],
        "followups": [
            {
                "id": "joint_injury",
                "question_text": "Did the pain start after a recent fall, heavy lifting, or physical injury?",
                "question_text_local": {
                    "kn": "ಇತ್ತೀಚೆಗೆ ಬಿದ್ದಿದ್ದಿರಾ ಅಥವಾ ಭಾರ ಎತ್ತುವುದರಿಂದ ನೋವು ಪ್ರಾರಂಭವಾಯಿತೇ?",
                    "hi": "क्या हाल ही में गिरने, भारी वजन उठाने या चोट लगने के बाद दर्द शुरू हुआ?",
                    "ta": "சமீபத்தில் கீழே விழுந்ததால் அல்லது பாரம் தூக்கியதால் வலி ஆரம்பித்ததா?",
                    "te": "ఇటీవల కింద పడటం లేదా బరువులు ఎత్తడం వల్ల నొప్పి ప్రారంభమైందా?"
                },
                "options": ["No injury, gradual onset", "Mild sprain / strain from physical work", "Severe fall / unable to bear weight"]
            },
            {
                "id": "joint_swelling",
                "question_text": "Is there noticeable redness, warmth, or swelling around the joint?",
                "question_text_local": {
                    "kn": "ಕೀಲುಗಳ ಸುತ್ತಲೂ ಊತ, ಕೆಂಪಾಗುವಿಕೆ ಅಥವಾ ಬಿಸಿ ಅನುಭವವಿದೆಯೇ?",
                    "hi": "क्या जोड़ के आसपास सूजन, लालिमा या गर्माहट महसूस हो रही है?",
                    "ta": "மூட்டைச் சுற்றி வீக்கம் அல்லது சிவத்தல் உள்ளதா?",
                    "te": "కీలు చుట్టూ వాపు లేదా ఎరుపుదనం ఉందా?"
                },
                "options": ["No swelling", "Mild swelling after walking", "Severe swelling and hot to touch"]
            }
        ],
        "specialist": "Orthopedic Doctor / Physiotherapist",
        "causes": ["Musculoskeletal strain", "Osteoarthritis / Age-related wear", "Post-viral reactive arthralgia (e.g. Chikungunya)", "Ligament sprain"],
        "precautions": [
            "Give rest to the affected joint and avoid heavy farm work or lifting.",
            "Apply a warm water bag or cool compress on painful joints for 15 minutes.",
            "Avoid sitting on the floor if knee pain is severe.",
            "Wear supportive footwear while walking on uneven rural terrain."
        ]
    },
    "skin_rash": {
        "keywords": ["skin", "itching", "rash", "allergy", "boil", "khujli", "chirkalu", "arippu", "durada", "ಚರ್ಮದ ತುರಿಕೆ", "ದದ್ದು", "खुजली", "चकत्ते", "தோல் அரிப்பு", "దురద"],
        "followups": [
            {
                "id": "rash_spread",
                "question_text": "Is the rash spreading rapidly or accompanied by pus/oozing?",
                "question_text_local": {
                    "kn": "ದದ್ದು ವೇಗವಾಗಿ ಹರಡುತ್ತಿದೆಯೇ ಅಥವಾ ಕೀವು ಬರುತ್ತಿದೆಯೇ?",
                    "hi": "क्या दाने तेजी से फैल रहे हैं या मवाद निकल रहा है?",
                    "ta": "தடிப்புகள் வேகமாக பரவுகிறதா அல்லது சீழ் வருகிறதா?",
                    "te": "దద్దుర్లు వేగంగా వ్యాపిస్తున్నాయా లేదా చీము కారుతోందా?"
                },
                "options": ["Localized dry itching", "Spreading patches across body", "Pus-filled blisters / painful sores"]
            }
        ],
        "specialist": "Dermatologist / General Physician",
        "causes": ["Fungal skin infection (Tinea)", "Contact dermatitis / Plant allergy", "Scabies", "Heat rash (Prickly heat)"],
        "precautions": [
            "Keep the affected skin clean and dry.",
            "Wear loose, clean cotton clothing.",
            "Do not scratch with nails to prevent secondary bacterial infection.",
            "Do not share personal towels, bedsheets, or clothes."
        ]
    }
}

def identify_matched_profile(text: str) -> Optional[Dict[str, Any]]:
    """Match patient's symptoms text with predefined clinical profiles."""
    text_lower = text.lower()
    for category, profile in SYMPTOM_PROFILES.items():
        for kw in profile["keywords"]:
            if kw.lower() in text_lower:
                return profile
    return None

def get_fallback_followup_questions(symptoms: str, language: str = "en") -> List[FollowupQuestion]:
    """Generate intelligent follow-up questions tailored to symptoms."""
    profile = identify_matched_profile(symptoms)
    if profile:
        raw_list = profile["followups"]
    else:
        # Default general clinical follow-up for unspecified complaints
        raw_list = [
            {
                "id": "duration_general",
                "question_text": "How long have you been experiencing these symptoms?",
                "question_text_local": {
                    "kn": "ಈ ಲಕ್ಷಣಗಳು ಎಷ್ಟು ದಿನಗಳಿಂದ ಇವೆ?",
                    "hi": "आपको ये लक्षण कितने समय से हैं?",
                    "ta": "இந்த அறிகுறிகள் எத்தனை நாட்களாக உள்ளன?",
                    "te": "ఈ లక్షణాలు ఎంతకాలంగా ఉన్నాయి?"
                },
                "options": ["Started today / sudden", "1 to 3 days", "About a week", "More than 2 weeks"]
            },
            {
                "id": "severity_general",
                "question_text": "How much are these symptoms affecting your daily activities?",
                "question_text_local": {
                    "kn": "ಈ ಲಕ್ಷಣಗಳು ನಿಮ್ಮ ದೈನಂದಿನ ಕೆಲಸಗಳಿಗೆ ಎಷ್ಟು ಅಡ್ಡಿಯುಂಟುಮಾಡುತ್ತಿವೆ?",
                    "hi": "ये लक्षण आपके दैनिक कार्यों को कितना प्रभावित कर रहे हैं?",
                    "ta": "இந்த அறிகுறிகள் உங்கள் அன்றாட பணிகளை எவ்வளவு பாதிக்கின்றன?",
                    "te": "ఈ లక్షణాలు మీ రోజువారీ పనులను ఎంతవరకు ప్రభావితం చేస్తున్నాయి?"
                },
                "options": ["Mild - I can do routine work", "Moderate - Feeling uncomfortable & resting", "Severe - Unable to get out of bed"]
            },
            {
                "id": "fever_associated",
                "question_text": "Do you also have fever, severe weakness, or loss of appetite?",
                "question_text_local": {
                    "kn": "ಜ್ವರ, ವಿಪರೀತ ನಿಶ್ಯಕ್ತಿ ಅಥವಾ ಹಸಿವಿಲ್ಲದಿರುವುದು ಇದೆಯೇ?",
                    "hi": "क्या बुखार, अत्यधिक कमजोरी या भूख न लगना भी है?",
                    "ta": "காய்ச்சல், அதிக சோர்வு அல்லது பசியின்மை உள்ளதா?",
                    "te": "జ్వరం, విపరీతమైన నీరసం లేదా ఆకలి లేకపోవడం కూడా ఉన్నాయా?"
                },
                "options": ["No fever or major weakness", "Mild fever / feeling warm", "High fever with chills"]
            }
        ]

    results = []
    for item in raw_list:
        local_text = item.get("question_text_local", {}).get(language, "")
        results.append(FollowupQuestion(
            id=item["id"],
            question_text=item["question_text"],
            question_text_local=local_text,
            input_type="select",
            options=item["options"]
        ))
    return results

def evaluate_risk_heuristic(symptoms: str, answers: Dict[str, str]) -> Tuple[str, List[str], str, List[str], str, str]:
    """
    Computes (risk_level, possible_causes, specialist, precautions, when_to_seek_care, summary).
    Risk is classified into Low Risk, Moderate Risk, or Emergency Risk.
    """
    profile = identify_matched_profile(symptoms)
    
    # Check severity from answers
    answers_str = " ".join(answers.values()).lower()
    
    # Emergency triggers in followups (if patient reported severe symptoms in followup)
    if any(k in answers_str for k in ["blood in phlegm", "more than 5 times (feeling weak/dizzy)", "severe fall / unable to bear weight", "sudden explosive", "neck stiffness with high fever", "yes, minor bleeding"]):
        risk = "Moderate Risk"
        if "neck stiffness" in answers_str or "blood in phlegm" in answers_str:
            risk = "Emergency Risk"
    elif any(k in answers_str for k in ["severe", "more than 5 days", "more than 2 weeks", "thick yellow", "lower right abdomen", "spreading patches"]):
        risk = "Moderate Risk"
    else:
        risk = "Low Risk"

    if profile:
        specialist = profile["specialist"]
        causes = profile["causes"]
        precautions = profile["precautions"]
    else:
        specialist = "General Physician"
        causes = ["General viral syndrome", "Fatigue / Mild dehydration", "Early localized infection", "Muscular strain"]
        precautions = [
            "Ensure adequate hydration with clean water, ORS, or warm fluids.",
            "Take adequate physical rest.",
            "Eat freshly prepared, light, easily digestible meals.",
            "Monitor body temperature and symptoms twice daily."
        ]

    if risk == "Emergency Risk":
        summary = (
            f"The combination of '{symptoms}' and reported critical signs indicates high urgency. "
            "Immediate hospital consultation at the nearest Primary Health Center (PHC) or Emergency Department is strongly advised."
        )
        when_to_seek = "Immediately. Do not wait or self-medicate."
    elif risk == "Moderate Risk":
        summary = (
            f"Based on your symptoms ('{symptoms}') and duration, your condition is classified as Moderate Risk. "
            f"You should be evaluated by a {specialist} at your nearby Primary Health Center (PHC) within 24 to 48 hours."
        )
        when_to_seek = "Visit your nearest health center or clinic within 24 to 48 hours, or sooner if symptoms worsen."
    else:
        summary = (
            f"Your reported symptoms ('{symptoms}') appear to be in the Low Risk category. "
            "Home supportive care and hydration should help. If symptoms persist beyond 3 days or intensify, visit a health worker or doctor."
        )
        when_to_seek = "If symptoms do not improve within 3 days or if new symptoms (like high fever or severe pain) appear."

    return risk, causes, specialist, precautions, when_to_seek, summary

async def call_gemini_triage(
    symptoms: str,
    answers: Dict[str, str],
    language: str = "en",
    age: Optional[int] = None,
    gender: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Calls Google Gemini API using httpx if GEMINI_API_KEY is available.
    Returns structured triage JSON or None if unavailable/fails.
    """
    if not GEMINI_API_KEY or len(GEMINI_API_KEY.strip()) < 10:
        return None

    prompt = f"""
You are RuralCare AI, an empathetic, highly trained medical triage assistant for rural health access.
Patient Context:
- Age: {age or 'Not specified'}
- Gender: {gender or 'Not specified'}
- Primary Symptoms: {symptoms}
- Follow-up Responses: {json.dumps(answers)}
- Target Language: {language}

Strict Guidelines:
1. Classify risk level into EXACTLY one of: "Low Risk", "Moderate Risk", "Emergency Risk".
2. If symptoms indicate acute danger (cardiac, stroke, respiratory collapse, heavy hemorrhage, poisoning), classify as "Emergency Risk".
3. NEVER claim to provide a definitive medical diagnosis. State that this is an informational health assessment.
4. Provide appropriate doctor specialization (e.g. "General Physician", "Pediatrician", "Gynecologist", "Orthopedic", etc.).
5. Provide practical, safe home care precautions suitable for rural contexts (clean boiled water, ORS, resting, avoiding unprescribed medicines).
6. Return your response in STRICT valid JSON format with this exact structure:
{{
  "risk_level": "Low Risk" | "Moderate Risk" | "Emergency Risk",
  "summary": "Clear, compassionate explanation of the assessment in plain language",
  "possible_causes": ["Possible cause 1", "Possible cause 2", "Possible cause 3"],
  "suggested_specialist": "Specialist title",
  "precautions": ["Actionable precaution 1", "Actionable precaution 2", "Actionable precaution 3"],
  "when_to_seek_care": "Clear guidance on timeframe to visit clinic or emergency",
  "summary_local": "Summary translated into {language} if {language} is not en"
}}
Do not include markdown code ticks outside the JSON string.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                return parsed
            else:
                logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.warning(f"Gemini API call failed or timed out: {e}. Falling back to heuristic clinical engine.")

    return None
