from app.services.triage_engine import check_emergency_rules
from app.services.ai_service import evaluate_risk_heuristic, get_fallback_followup_questions

def test_emergency_rule_cardiac_english():
    text = "I have crushing chest pain radiating to left arm and sweating"
    result = check_emergency_rules(text, language="en")
    assert result is not None
    assert result["is_emergency"] is True
    assert result["risk_level"] == "Emergency Risk"
    assert "Cardiac" in result["category"]

def test_emergency_rule_snakebite_kannada():
    text = "ನನ್ನ ಕಾಲಿಗೆ ಹಾವು ಕಡಿತವಾಗಿದೆ ವಿಪರೀತ ಊತ ಬಂದಿದೆ"
    result = check_emergency_rules(text, language="kn")
    assert result is not None
    assert result["is_emergency"] is True
    assert result["risk_level"] == "Emergency Risk"
    assert "Toxicology" in result["category"]

def test_emergency_rule_respiratory_hindi():
    text = "मरीज को सांस लेने में भारी तकलीफ हो रही है और होंठ नीले पड़ रहे हैं"
    result = check_emergency_rules(text, language="hi")
    assert result is not None
    assert result["is_emergency"] is True
    assert result["risk_level"] == "Emergency Risk"

def test_emergency_rule_stroke_tamil():
    text = "அவருக்கு திடீர் பக்கவாதம் மற்றும் வாய் கோணல் வந்துள்ளது"
    result = check_emergency_rules(text, language="ta")
    assert result is not None
    assert result["is_emergency"] is True

def test_emergency_rule_unresponsive_telugu():
    text = "రోగి స్పృహ తప్పి పడిపోయాడు"
    result = check_emergency_rules(text, language="te")
    assert result is not None
    assert result["is_emergency"] is True

def test_non_emergency_mild_symptom():
    text = "I have mild sore throat and runny nose since morning"
    result = check_emergency_rules(text, language="en")
    assert result is None  # Should not falsely trigger emergency!

def test_followup_questions_generation():
    questions = get_fallback_followup_questions("Fever with headache", language="en")
    assert len(questions) > 0
    assert any("fever" in q.id.lower() or "duration" in q.id.lower() for q in questions)

def test_heuristic_triage_evaluation():
    risk, causes, specialist, precautions, when_to_seek, summary = evaluate_risk_heuristic(
        symptoms="Fever with chills",
        answers={"fever_duration": "3 to 5 days", "fever_severity": "Mild chills"}
    )
    assert risk in ["Low Risk", "Moderate Risk"]
    assert len(causes) > 0
    assert len(precautions) > 0
    assert "Physician" in specialist
