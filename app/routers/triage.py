import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_db_connection
from app.models import (
    TriageInitialRequest, TriageFollowupRequest, TriageResponse,
    FollowupQuestion, AssessmentRecord
)
from app.services.triage_engine import check_emergency_rules
from app.services.ai_service import (
    get_fallback_followup_questions,
    evaluate_risk_heuristic,
    call_gemini_triage
)
from app.services.auth_service import get_current_patient_optional

router = APIRouter(prefix="/api/triage", tags=["Symptom Checker & Triage"])

@router.post("/assess", response_model=TriageResponse)
async def assess_initial_symptoms(
    req: TriageInitialRequest,
    current_patient: Optional[dict] = Depends(get_current_patient_optional)
):
    """
    Step 1: Check symptoms against deterministic Emergency Safety Layer FIRST.
    If emergency detected -> halt, flash red SOS alert, do not delay care.
    If not emergency -> generate smart follow-up questions for deeper analysis.
    """
    # 1. Deterministic Rule-Based Emergency Safety Check
    emergency_trigger = check_emergency_rules(req.symptoms, req.language)
    if emergency_trigger:
        # Immediately record assessment in DB
        patient_id = req.patient_id or (current_patient["id"] if current_patient else None)
        patient_name = current_patient["name"] if current_patient else "Anonymous Patient"

        conn = get_db_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO assessments (
                    patient_id, patient_name, age, gender, location, primary_symptoms,
                    risk_level, is_emergency_rule, rule_triggered, ai_summary,
                    suggested_specialist, home_care_precautions, when_to_seek_care, language
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id, patient_name, req.age, req.gender, req.location, req.symptoms,
                "Emergency Risk", emergency_trigger["rule_name"],
                f"EMERGENCY DETECTED: {emergency_trigger['rule_name']}. Immediate medical intervention required.",
                emergency_trigger["specialist"],
                json.dumps([emergency_trigger["first_aid"]]),
                "IMMEDIATELY - CALL 108 AMBULANCE NOW",
                req.language
            ))
            conn.commit()
            assessment_id = cursor.lastrowid
        finally:
            conn.close()

        return TriageResponse(
            risk_level="Emergency Risk",
            is_emergency=True,
            emergency_action=emergency_trigger["first_aid"],
            rule_triggered=emergency_trigger["rule_name"],
            summary=f"CRITICAL HEALTH ALERT: {emergency_trigger['rule_name']} detected. Life-saving medical intervention is required without any delay.",
            possible_causes=[emergency_trigger["rule_name"], "Acute Medical Emergency"],
            suggested_specialist=emergency_trigger["specialist"],
            precautions=[emergency_trigger["first_aid"]],
            when_to_seek_care="Immediately. Dial 108 or reach the nearest Emergency Department now.",
            followup_questions=[],
            assessment_id=assessment_id
        )

    # 2. Not an immediate emergency -> generate tailored follow-up questions
    followup_questions = get_fallback_followup_questions(req.symptoms, req.language)

    return TriageResponse(
        risk_level="Evaluating",
        is_emergency=False,
        summary=f"Symptom entered: '{req.symptoms}'. Please answer these follow-up questions to help determine urgency and recommend the right care.",
        possible_causes=[],
        suggested_specialist="General Physician",
        precautions=[],
        when_to_seek_care="Evaluating based on follow-up responses...",
        followup_questions=followup_questions
    )

@router.post("/followup", response_model=TriageResponse)
async def evaluate_followup(
    req: TriageFollowupRequest,
    current_patient: Optional[dict] = Depends(get_current_patient_optional)
):
    """
    Step 2: Combine initial symptoms + follow-up answers.
    Analyzes with Gemini AI (or Heuristic Clinical Engine fallback) and classifies risk.
    """
    patient_id = req.patient_id or (current_patient["id"] if current_patient else None)
    patient_name = current_patient["name"] if current_patient else "Anonymous Patient"

    # Try Gemini AI first if configured
    ai_result = await call_gemini_triage(
        symptoms=req.initial_symptoms,
        answers=req.answers,
        language=req.language,
        age=req.age,
        gender=req.gender
    )

    if ai_result:
        risk_level = ai_result.get("risk_level", "Moderate Risk")
        summary = ai_result.get("summary_local") or ai_result.get("summary", "")
        possible_causes = ai_result.get("possible_causes", [])
        suggested_specialist = ai_result.get("suggested_specialist", "General Physician")
        precautions = ai_result.get("precautions", [])
        when_to_seek = ai_result.get("when_to_seek_care", "Within 24-48 hours")
    else:
        # High quality heuristic clinical model
        risk_level, possible_causes, suggested_specialist, precautions, when_to_seek, summary = evaluate_risk_heuristic(
            req.initial_symptoms, req.answers
        )

    is_emergency = (risk_level == "Emergency Risk")

    # Save complete assessment to DB
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO assessments (
                patient_id, patient_name, age, gender, location, primary_symptoms,
                followup_answers, risk_level, is_emergency_rule, rule_triggered,
                ai_summary, potential_causes, suggested_specialist, home_care_precautions,
                when_to_seek_care, language
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id, patient_name, req.age, req.gender, req.location, req.initial_symptoms,
            json.dumps(req.answers), risk_level, summary, json.dumps(possible_causes),
            suggested_specialist, json.dumps(precautions), when_to_seek, req.language
        ))
        conn.commit()
        assessment_id = cursor.lastrowid
    finally:
        conn.close()

    return TriageResponse(
        risk_level=risk_level,
        is_emergency=is_emergency,
        emergency_action="Call 108 or reach the nearest hospital immediately" if is_emergency else None,
        summary=summary,
        possible_causes=possible_causes,
        suggested_specialist=suggested_specialist,
        precautions=precautions,
        when_to_seek_care=when_to_seek,
        followup_questions=[],
        assessment_id=assessment_id
    )

@router.get("/history", response_model=List[AssessmentRecord])
def get_patient_history(
    patient_id: Optional[int] = None,
    current_patient: Optional[dict] = Depends(get_current_patient_optional)
):
    """Retrieve history of assessments for a patient."""
    effective_patient_id = patient_id or (current_patient["id"] if current_patient else None)
    
    conn = get_db_connection()
    try:
        if effective_patient_id:
            rows = conn.execute(
                "SELECT * FROM assessments WHERE patient_id = ? ORDER BY created_at DESC",
                (effective_patient_id,)
            ).fetchall()
        else:
            # Return recent assessments across demo
            rows = conn.execute(
                "SELECT * FROM assessments ORDER BY created_at DESC LIMIT 20"
            ).fetchall()

        records = []
        for r in rows:
            d = dict(r)
            d["is_emergency_rule"] = bool(d.get("is_emergency_rule", 0))
            if d.get("followup_answers"):
                try:
                    d["followup_answers"] = json.loads(d["followup_answers"])
                except Exception:
                    pass
            if d.get("potential_causes"):
                try:
                    d["potential_causes"] = json.loads(d["potential_causes"])
                except Exception:
                    pass
            if d.get("home_care_precautions"):
                try:
                    d["home_care_precautions"] = json.loads(d["home_care_precautions"])
                except Exception:
                    pass
            records.append(AssessmentRecord(**d))
        return records
    finally:
        conn.close()

@router.get("/history/{assessment_id}", response_model=AssessmentRecord)
def get_assessment_detail(assessment_id: int):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assessment not found")
        d = dict(row)
        d["is_emergency_rule"] = bool(d.get("is_emergency_rule", 0))
        if d.get("followup_answers"):
            try:
                d["followup_answers"] = json.loads(d["followup_answers"])
            except Exception:
                pass
        if d.get("potential_causes"):
            try:
                d["potential_causes"] = json.loads(d["potential_causes"])
            except Exception:
                pass
        if d.get("home_care_precautions"):
            try:
                d["home_care_precautions"] = json.loads(d["home_care_precautions"])
            except Exception:
                pass
        return AssessmentRecord(**d)
    finally:
        conn.close()
