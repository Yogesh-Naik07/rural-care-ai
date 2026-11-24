"""
Rule-Based Emergency Safety Layer and Clinical Triage Rules.
Transparent, deterministic emergency rules that run BEFORE any LLM inference
to ensure emergency symptoms are NEVER missed or delayed.
"""

import re
from typing import Dict, Any, Optional, Tuple, List

# Emergency Rule Definitions with multi-language keywords & clinical rationales
EMERGENCY_RULES: List[Dict[str, Any]] = [
    {
        "id": "EMERG_CARDIAC",
        "name": "Acute Coronary / Severe Cardiac Warning",
        "category": "Cardiac",
        "patterns": [
            r"\b(chest\s+pain|chest\s+pressure|heart\s+attack|crushing\s+chest|pain\s+radiating\s+to\s+(left\s+arm|jaw|neck))\b",
            r"\b(heavy\s+chest|chest\s+tightness\s+with\s+sweat|angina)\b",
            # Hindi
            r"(सीने\s*में\s*दर्द|छाती\s*में\s*दर्द|दिल\s*का\s*दौरा|seene\s*mein\s*dard|chhati\s*me\s*dard)",
            # Kannada
            r"(ಎದೆ\s*ನೋವು|ಹೃದಯಾಘಾತ|ede\s*novu|ede\s*bhara|ede\s*hathira\s*novu)",
            # Tamil
            r"(நெஞ்சு\s*வலி|மாரடைப்பு|nenju\s*vali|maaradaipu)",
            # Telugu
            r"(గుండె\s*నొప్పి|ఛాతీ\s*నొప్పి|gunde\s*noppi|chathi\s*noppi)"
        ],
        "first_aid": {
            "en": "Call 108 ambulance immediately! Keep patient calm and seated upright. Loosen tight clothing around neck and chest. Do not allow patient to walk or exert themselves. If prescribed, assist with Sorbitrate/Nitroglycerin under tongue.",
            "hi": "तुरंत 108 एम्बुलेंस को कॉल करें! मरीज को शांत और सीधा बैठाएं। गर्दन और छाती के कपड़े ढीले करें। मरीज को चलने न दें।",
            "kn": "ಕೂಡಲೇ 108 ಆಂಬ್ಯುಲೆನ್ಸ್‌ಗೆ ಕರೆ ಮಾಡಿ! ರೋಗಿಯನ್ನು ಶಾಂತವಾಗಿ ಕೂರಿಸಿ. ಬಿಗಿಯಾದ ಬಟ್ಟೆ ಸಡಿಲಗೊಳಿಸಿ. ನಡೆಯಲು ಬಿಡಬೇಡಿ.",
            "ta": "உடனடியாக 108 ஆம்புலன்ஸை அழைக்கவும்! நோயாளியை அமைதியாக உட்கார வைக்கவும். இறுக்கமான ஆடைகளை தளர்த்தவும்.",
            "te": "వెంటనే 108 అంబులెన్స్‌కు కాల్ చేయండి! రోగిని నిటారుగా కూర్చోబెట్టండి. గట్టి దుస్తులను వదులు చేయండి."
        },
        "specialist": "Emergency Medicine / Cardiologist"
    },
    {
        "id": "EMERG_RESPIRATORY",
        "name": "Severe Respiratory Distress / Suffocation",
        "category": "Respiratory",
        "patterns": [
            r"\b(cannot\s+breathe|gasping\s+for\s+air|suffocating|blue\s+lips|choking|unable\s+to\s+breathe|severe\s+breathlessness|stridor)\b",
            # Hindi
            r"(सांस\s*लेने\s*में\s*भारी\s*तकलीफ|दम\s*घुट\s*रहा|नीले\s*होंठ|saans\s*nahi\s*aa\s*rahi|dum\s*ghutna)",
            # Kannada
            r"(ಉಸಿರಾಟದ\s*ತೊಂದರೆ|ಉಸಿರು\s*ಕಟ್ಟುವುದು|usiru\s*katuvike|usiradata\s*kashta)",
            # Tamil
            r"(மூச்சு\s*திணறல்|மூச்சு\s*விட\s*முடியவில்லை|moochu\s*thinaval)",
            # Telugu
            r"(శ్వాస\s*తీసుకోవడంలో\s*తీవ్ర\s*ఇబ్బంది|ఊపిరాడటం\s*లేదు|swasa\s*aagipovatam)"
        ],
        "first_aid": {
            "en": "Call 108 immediately! Sit the patient leaning slightly forward. Ensure fresh airflow and open windows. Do not crowd the patient. If asthmatic, administer rescue inhaler immediately.",
            "hi": "तुरंत 108 पर कॉल करें! मरीज को आगे की ओर झुकाकर बैठाएं। ताजी हवा आने दें। यदि अस्थमा है तो इनहेलर दें।",
            "kn": "ತಕ್ಷಣ 108 ಗೆ ಕರೆ ಮಾಡಿ! ರೋಗಿಯನ್ನು ಮುಂದಕ್ಕೆ ಬಾಗಿಸಿ ಕೂರಿಸಿ. ಕಿಟಕಿಗಳನ್ನು ತೆರೆದು ತಾಜಾ ಗಾಳಿ ಬರುವಂತೆ ಮಾಡಿ.",
            "ta": "உடனே 108 அழைக்கவும்! நோயாளியை சற்று முன்னோக்கி சாய்த்து உட்கார வைக்கவும். காற்றோட்டம் கிடைப்பதை உறுதிசெய்யவும்.",
            "te": "వెంటనే 108కి కాల్ చేయండి! రోగిని కాస్త ముందుకు వంచి కూర్చోబెట్టండి. గాలి బాగా ఆడేలా చూడండి."
        },
        "specialist": "Emergency Medicine / Pulmonologist"
    },
    {
        "id": "EMERG_STROKE",
        "name": "Acute Stroke / FAST Signs (Face, Arm, Speech)",
        "category": "Neurological",
        "patterns": [
            r"\b(stroke|facial\s+droop|slurred\s+speech|paralysis|sudden\s+numbness|loss\s+of\s+speech|sudden\s+weakness\s+on\s+one\s+side)\b",
            # Hindi
            r"(लकवा|मुंह\s*टेढ़ा|बोलने\s*में\s*लड़खड़ाहट|एक\s*तरफ\s*कमजोरी|lakwa|bol\s*nahi\s*pa\s*raha)",
            # Kannada
            r"(ಪಾರ್ಶ್ವವಾಯು|ಮುಖ\s*ಡೊಂಕು|ಮಾತು\s*ತಡವರಿಸುವುದು|parshwavayu|mukha\s*donku)",
            # Tamil
            r"(பக்கவாதம்|வாய்\s*கோணல்|பேச்சு\s*குளறுதல்|pakkavatham)",
            # Telugu
            r"(పక్షవాతం|ముఖం\s*వంకర|మాట\s*ముద్దగారడం|pakshavatham)"
        ],
        "first_aid": {
            "en": "TIME IS BRAIN! Call 108 immediately. Note the exact time symptoms started. Lay patient on their side (recovery position) if drowsy. Do NOT give food, water, or medicine by mouth.",
            "hi": "समय अत्यंत महत्वपूर्ण है! तुरंत 108 पर कॉल करें। लक्षण शुरू होने का समय नोट करें। मरीज को कुछ भी खाने-पीने को न दें।",
            "kn": "ಸಮಯ ಬಹಳ ಮುಖ್ಯ! ತಕ್ಷಣ 108 ಗೆ ಕರೆ ಮಾಡಿ. ರೋಗಿಗೆ ಬಾಯಿಯ ಮೂಲಕ ಯಾವುದೇ ಆಹಾರ ಅಥವಾ ನೀರನ್ನು ನೀಡಬೇಡಿ.",
            "ta": "நேரம் மிக முக்கியம்! உடனடியாக 108 அழைக்கவும். வாயில் தண்ணீர் அல்லது மருந்து எதுவும் கொடுக்க வேண்டாம்.",
            "te": "సమయం చాలా విలువైంది! వెంటనే 108కి కాల్ చేయండి. రోగికి నీళ్లు గానీ ఆహారం గానీ ఇవ్వవద్దు."
        },
        "specialist": "Neurologist / Emergency Medicine"
    },
    {
        "id": "EMERG_UNRESPONSIVE",
        "name": "Unresponsiveness / Prolonged Seizure / Coma",
        "category": "Neurological",
        "patterns": [
            r"\b(unconscious|fainted\s+and\s+not\s+waking|not\s+responding|seizure|convulsion|epilepsy\s+fit|passed\s+out)\b",
            # Hindi
            r"(बेहोश|मूर्छित|होश\s*नहीं\s*आ\s*रहा|दौरा|मिर्गी|behosh|dora\b)",
            # Kannada
            r"(ಪ್ರಜ್ಞಾಹೀನ|ಎಚ್ಚರವಾಗುತ್ತಿಲ್ಲ|ಫಿಟ್ಸ್|ಮೂರ್ಛೆ|prajnaheena|fits)",
            # Tamil
            r"(மயக்கம்|நினைவிழப்பு|வலிப்பு|mayakkam|valippu)",
            # Telugu
            r"(స్పృహ\s*తప్పి|స్పృహ\s*తప్పడం|స్పృహ\s*లేదు|మేల్కొనడం\s*లేదు|ఫిట్స్|spruha\s*thapp|fits)"
        ],
        "first_aid": {
            "en": "Check breathing. Turn patient onto their left side in recovery position to keep airway clear. Clear area of sharp objects. Do NOT insert keys, spoons or fingers into mouth. Call 108 immediately.",
            "kn": "ಉಸಿರಾಟ ಪರೀಕ್ಷಿಸಿ. ರೋಗಿಯನ್ನು ಎಡಭಾಗಕ್ಕೆ ತಿರುಗಿಸಿ ಮಲಗಿಸಿ. ಬಾಯಿಗೆ ಚಮಚ, ಕೀಲಿ ಕೈ ಇಡಬೇಡಿ. ತಕ್ಷಣ 108 ಗೆ ಕರೆ ಮಾಡಿ.",
            "hi": "सांस की जांच करें। मरीज को बाईं करवट लिटाएं। मुंह में चम्मच या चाबी न डालें। तुरंत 108 पर कॉल करें।",
            "ta": "சுவாசத்தை சரிபார்க்கவும். நோயாளியை இடது பக்கமாக ஒருக்களித்து படுக்க வைக்கவும். வாயில் எதையும் வைக்க வேண்டாம்.",
            "te": "శ్వాసను పరిశీలించండి. రోగిని ఎడమ వైపునకు తిప్పి పడుకోబెట్టండి. నోట్లో తాళాలు లేదా చెంచాలు పెట్టవద్దు."
        },
        "specialist": "Emergency Medicine / Neurologist"
    },
    {
        "id": "EMERG_SNAKEBITE",
        "name": "Snakebite / Severe Envenomation / Poisoning",
        "category": "Toxicology",
        "patterns": [
            r"\b(snake\s*bite|poison|pesticide|swallowed\s+chemical|insecticide|scorpion\s+sting)\b",
            # Hindi
            r"(सांप\s*काटा|सांप\s*ने\s*काटा|ज़हर|कीटनाशक|saanp\s*kata|zeher)",
            # Kannada
            r"(ಹಾವು\s*ಕಡಿತ|ವಿಷ|ಕೀಟನಾಶಕ|ಚೇಳು\s*ಕುಟುಕು|haavu\s*kaditha|visha)",
            # Tamil
            r"(பாம்பு\s*கடி|விஷம்|பூச்சிக்கொல்லி|pambu\s*kadi|visham)",
            # Telugu
            r"(పాము\s*కాటు|విషం|పురుగుల\s*మందు|pamu\s*kaatu|visham)"
        ],
        "first_aid": {
            "en": "EMERGENCY! Keep patient completely still and calm to slow venom spread. Immobilize the bitten limb below heart level. Do NOT cut, suck venom, apply ice, or use tight tourniquets. Transport immediately to the nearest hospital with Anti-Snake Venom (ASV).",
            "kn": "ತುರ್ತು ಪರಿಸ್ಥಿತಿ! ರೋಗಿಯನ್ನು ಶಾಂತವಾಗಿರಿಸಿ. ಕಚ್ಚಿದ ಜಾಗವನ್ನು ಕತ್ತರಿಸಬೇಡಿ ಅಥವಾ ರಕ್ತ ಹೀರುವ ಪ್ರಯತ್ನ ಮಾಡಬೇಡಿ. ತಕ್ಷಣವೇ ಹಾವು ಕಡಿತಕ್ಕೆ ಮದ್ದು (ASV) ಇರುವ ಆಸ್ಪತ್ರೆಗೆ ಕರೆದೊಯ್ಯಿರಿ.",
            "hi": "आपातकालीन स्थिति! मरीज को बिल्कुल शांत रखें। काटे गए स्थान को काटें या चूसें नहीं। बर्फ या कसकर पट्टी न बांधें। तुरंत नजदीकी अस्पताल ले जाएं।",
            "ta": "அவசரநிலை! விஷம் பரவுவதை குறைக்க நோயாளியை அசையாமல் வைக்கவும். கடித்த இடத்தை அறுக்கவோ உறிஞ்சவோ கூடாது. உடனடியாக மருத்துவமனைக்கு செல்லவும்.",
            "te": "అత్యవసరం! విషం వేగంగా వ్యాపించకుండా రోగిని కదలకుండా ఉంచండి. గాటు పెట్టడం లేదా రక్తం పీల్చడం చేయవద్దు. వెంటనే ఆసుపత్రికి తరలించండి."
        },
        "specialist": "Emergency Medicine / Toxicology"
    },
    {
        "id": "EMERG_HEMORRHAGE",
        "name": "Severe Uncontrolled Bleeding / Arterial Hemorrhage",
        "category": "Trauma",
        "patterns": [
            r"\b(heavy\s+bleeding|severe\s+bleeding|blood\s+spurting|uncontrolled\s+bleeding|deep\s+cut\s+bleeding|stab\s+wound)\b",
            # Hindi
            r"(भारी\s*रक्तस्राव|खून\s*बहना\s*बंद\s*नहीं\s*हो\s*रहा|khoon\s*behna)",
            # Kannada
            r"(ವಿಪರೀತ\s*ರಕ್ತಸ್ರಾವ|ರಕ್ತ\s*ನಿಲ್ಲುತ್ತಿಲ್ಲ|raktha\s*nilluthilla)",
            # Tamil
            r"(அதிக\s*இரத்தப்போக்கு|ரத்தம்\s*நிற்கவில்லை|raththa\s*pokku)",
            # Telugu
            r"(తీవ్రమైన\s*రక్తస్రావం|రక్తం\s*ఆగడం\s*లేదు|raktham\s*aagadam\s*ledu)"
        ],
        "first_aid": {
            "en": "Apply firm, continuous direct pressure to the wound using a clean cloth or bandage. Elevate the injured limb if possible. Do not remove the cloth if soaked; add another layer on top. Call 108 immediately.",
            "kn": "ಗಾಯದ ಮೇಲೆ ಶುಭ್ರವಾದ ಬಟ್ಟೆಯಿಂದ ಗಟ್ಟಿಯಾಗಿ ಒತ್ತಿ ಹಿಡಿಯಿರಿ. ರಕ್ತಸ್ರಾವ ನಿಲ್ಲುವವರೆಗೆ ಒತ್ತಡ ಬಿಡಬೇಡಿ. ತಕ್ಷಣ 108 ಕರೆ ಮಾಡಿ.",
            "hi": "साफ कपड़े से घाव पर सीधा और मजबूत दबाव बनाएं। यदि संभव हो तो अंग को ऊपर उठाएं। तुरंत 108 पर कॉल करें।",
            "ta": "சுத்தமான துணியால் காயத்தின் மீது நேரடியாக அழுத்தம் கொடுக்கவும். ரத்தப்போக்கு நிற்கும் வரை அழுத்தவும். உடனே 108 அழைக்கவும்.",
            "te": "శుభ్రమైన గుడ్డతో గాయంపై గట్టిగా అదిమి పట్టి ఉంచండి. వెంటనే 108 కి కాల్ చేయండి."
        },
        "specialist": "General Surgeon / Trauma Emergency"
    },
    {
        "id": "EMERG_ANAPHYLAXIS",
        "name": "Severe Allergic Shock / Anaphylaxis",
        "category": "Allergy",
        "patterns": [
            r"\b(anaphylaxis|swollen\s+tongue|swollen\s+throat|throat\s+closing|severe\s+allergic\s+reaction)\b",
            # Hindi
            r"(गले\s*में\s*सूजन|जीभ\s*का\s*फूलना|गला\s*घुट\s*रहा\s*एलर्जी|gale\s*me\s*sujan)",
            # Kannada
            r"(ನಾಲಿಗೆ\s*ಊತ|ಗಂಟಲು\s*ಊತ|ತೀವ್ರ\s*ಅಲರ್ಜಿ|nalige\s*ootha)",
            # Tamil
            r"(நாக்கு\s*வீக்கம்|தொண்டை\s*அடைப்பு|தீவிர\s*ஒவ்வாமை|naakku\s*veekkam)",
            # Telugu
            r"(నాలుక\s*వాపు|గొంతు\s*వాపు|తీవ్రమైన\s*అలర్జీ|gonthu\s*vaapu)"
        ],
        "first_aid": {
            "en": "Call 108 immediately! If the patient has an epinephrine auto-injector (EpiPen), administer it into outer thigh immediately. Lay patient flat with legs elevated unless they have difficulty breathing.",
            "kn": "ತಕ್ಷಣ 108 ಗೆ ಕರೆ ಮಾಡಿ! ಉಸಿರಾಟ ಸುಲಭವಾಗುವಂತೆ ಮಾಡಿ. ರೋಗಿಯನ್ನು ತಕ್ಷಣವೇ ತುರ್ತು ಚಿಕಿತ್ಸಾ ಕೇಂದ್ರಕ್ಕೆ ಕೊಂಡೊಯ್ಯಿರಿ.",
            "hi": "तुरंत 108 पर कॉल करें! मरीज को सीधा लिटाकर पैर थोड़े ऊपर उठाएं। तुरंत नजदीकी अस्पताल ले जाएं।",
            "ta": "உடனடியாக 108 அழைக்கவும்! உடனடியாக அருகிலுள்ள அவசர சிகிச்சைப் பிரிவுக்கு அழைத்துச் செல்லுங்கள்.",
            "te": "వెంటనే 108కి కాల్ చేయండి! శ్వాస తీసుకోవడం కష్టంగా ఉంటే రోగిని కూర్చోబెట్టి వెంటనే ఆసుపత్రికి తీసుకెళ్లండి."
        },
        "specialist": "Emergency Medicine / Immunologist"
    }
]

def check_emergency_rules(text: str, language: str = "en") -> Optional[Dict[str, Any]]:
    """
    Evaluates text against deterministic emergency red-flag rules.
    Returns emergency alert dictionary if triggered, else None.
    """
    clean_text = text.lower().strip()
    
    for rule in EMERGENCY_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, clean_text, re.IGNORECASE):
                # Matched an emergency rule!
                first_aid_msg = rule["first_aid"].get(language) or rule["first_aid"].get("en")
                return {
                    "is_emergency": True,
                    "risk_level": "Emergency Risk",
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "category": rule["category"],
                    "specialist": rule["specialist"],
                    "first_aid": first_aid_msg,
                    "matched_pattern": pattern
                }
    return None
