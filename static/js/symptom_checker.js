/**
 * RuralCare AI - Symptom Checker & Triage Controller
 */

let currentInitialSymptoms = "";
let currentFollowupQuestions = [];
let currentAssessmentResult = null;

function setQuickSymptom(text) {
    const input = document.getElementById("symptomInput");
    if (input) {
        input.value = text;
        input.focus();
    }
}

async function analyzeInitialSymptoms() {
    const input = document.getElementById("symptomInput");
    const symptoms = input ? input.value.trim() : "";

    if (!symptoms || symptoms.length < 2) {
        alert(t("inputPlaceholder"));
        return;
    }

    currentInitialSymptoms = symptoms;
    showCheckerLoading(true);
    hideAllCheckerSections();

    // Patient metadata if logged in
    const patient = Auth.getPatient();
    const payload = {
        symptoms: symptoms,
        language: currentLanguage,
        patient_id: patient ? patient.id : null,
        age: patient ? patient.age : null,
        gender: patient ? patient.gender : null,
        location: patient ? (patient.village + ", " + patient.district) : null
    };

    try {
        const resp = await fetch("/api/triage/assess", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...Auth.getAuthHeader()
            },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();
        showCheckerLoading(false);

        if (data.is_emergency) {
            // Immediate Rule-Based Emergency Triggered!
            renderEmergencyScreen(data);
        } else {
            // Render Follow-up Questions
            currentFollowupQuestions = data.followup_questions || [];
            if (currentFollowupQuestions.length > 0) {
                renderFollowupQuestions(currentFollowupQuestions);
            } else {
                // Directly submit if no followups needed
                submitFollowupAnswers({});
            }
        }
    } catch (err) {
        showCheckerLoading(false);
        console.error("Error analyzing symptoms:", err);
        alert("Failed to analyze symptoms. Please check network connection.");
    }
}

function renderEmergencyScreen(data) {
    const emergSection = document.getElementById("emergencyAlertSection");
    if (!emergSection) return;

    emergSection.classList.remove("d-none");
    document.getElementById("emergencyTitle").innerText = data.rule_triggered || t("emergencyAlertHeading");
    document.getElementById("emergencySummary").innerText = data.summary;
    document.getElementById("emergencyActionText").innerText = data.emergency_action || t("emergencyCallAction");

    // Speak emergency guidance in the patient's language immediately
    const emergencySpeech = `${t("emergencyAlertHeading")}. ${data.summary}. ${data.emergency_action || ""}`;
    VoiceAssistant.speak(emergencySpeech);

    // Scroll smoothly to alert
    emergSection.scrollIntoView({ behavior: "smooth" });
}

function renderFollowupQuestions(questions) {
    const section = document.getElementById("followupSection");
    const container = document.getElementById("followupQuestionsContainer");
    if (!section || !container) return;

    container.innerHTML = "";

    questions.forEach((q, idx) => {
        const qCard = document.createElement("div");
        qCard.className = "card question-card mb-3 p-3 shadow-sm border-0";
        
        const qText = (currentLanguage !== "en" && q.question_text_local) ? q.question_text_local : q.question_text;

        let optionsHtml = "";
        q.options.forEach((opt, optIdx) => {
            const optId = `q_${q.id}_opt_${optIdx}`;
            optionsHtml += `
                <div class="form-check custom-option-pill my-2">
                    <input class="form-check-input" type="radio" name="q_${q.id}" id="${optId}" value="${opt}" ${optIdx === 0 ? "checked" : ""}>
                    <label class="form-check-label w-100" for="${optId}">
                        ${opt}
                    </label>
                </div>
            `;
        });

        qCard.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <span class="badge bg-primary rounded-circle me-2 px-2 py-1">${idx + 1}</span>
                <h6 class="mb-0 fw-bold">${qText}</h6>
            </div>
            <div class="options-container ms-3">
                ${optionsHtml}
            </div>
        `;
        container.appendChild(qCard);
    });

    section.classList.remove("d-none");
    section.scrollIntoView({ behavior: "smooth" });
}

async function submitFollowupAnswers(customAnswers = null) {
    let answers = {};

    if (customAnswers) {
        answers = customAnswers;
    } else {
        currentFollowupQuestions.forEach(q => {
            const selected = document.querySelector(`input[name="q_${q.id}"]:checked`);
            if (selected) {
                answers[q.id] = selected.value;
            }
        });
    }

    showCheckerLoading(true);
    const section = document.getElementById("followupSection");
    if (section) section.classList.add("d-none");

    const patient = Auth.getPatient();
    const payload = {
        initial_symptoms: currentInitialSymptoms,
        answers: answers,
        language: currentLanguage,
        patient_id: patient ? patient.id : null,
        age: patient ? patient.age : null,
        gender: patient ? patient.gender : null,
        location: patient ? (patient.village + ", " + patient.district) : null
    };

    try {
        const resp = await fetch("/api/triage/followup", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...Auth.getAuthHeader()
            },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();
        showCheckerLoading(false);
        currentAssessmentResult = data;
        renderAssessmentResults(data);
    } catch (err) {
        showCheckerLoading(false);
        console.error("Error submitting followup:", err);
        alert("Failed to complete triage. Please try again.");
    }
}

function renderAssessmentResults(data) {
    const resSection = document.getElementById("resultsSection");
    if (!resSection) return;

    // Risk badge styling
    const badge = document.getElementById("riskBadge");
    badge.className = "badge fs-6 px-3 py-2";

    if (data.risk_level === "Emergency Risk") {
        badge.classList.add("bg-danger");
        badge.innerText = t("riskEmergency");
    } else if (data.risk_level === "Moderate Risk") {
        badge.classList.add("bg-warning", "text-dark");
        badge.innerText = t("riskModerate");
    } else {
        badge.classList.add("bg-success");
        badge.innerText = t("riskLow");
    }

    // Summary & Specialist
    document.getElementById("resultSummary").innerText = data.summary;
    document.getElementById("suggestedSpecialist").innerText = data.suggested_specialist || "General Physician";

    // Possible causes
    const causesContainer = document.getElementById("possibleCausesList");
    causesContainer.innerHTML = "";
    if (data.possible_causes && data.possible_causes.length > 0) {
        data.possible_causes.forEach(cause => {
            const li = document.createElement("li");
            li.className = "list-group-item";
            li.innerHTML = `<i class="fa-solid fa-circle-info text-primary me-2"></i> ${cause}`;
            causesContainer.appendChild(li);
        });
    }

    // Precautions
    const precautionsContainer = document.getElementById("precautionsList");
    precautionsContainer.innerHTML = "";
    if (data.precautions && data.precautions.length > 0) {
        data.precautions.forEach(prec => {
            const li = document.createElement("li");
            li.className = "list-group-item";
            li.innerHTML = `<i class="fa-solid fa-check text-success me-2"></i> ${prec}`;
            precautionsContainer.appendChild(li);
        });
    }

    // When to seek care
    document.getElementById("whenToSeekText").innerText = data.when_to_seek_care;

    // Doctor finder shortcut button
    const findDocBtn = document.getElementById("findDocShortcutBtn");
    if (findDocBtn) {
        findDocBtn.onclick = () => {
            App.navigate("doctors");
            filterDoctorsBySpecialty(data.suggested_specialist);
        };
    }

    resSection.classList.remove("d-none");
    resSection.scrollIntoView({ behavior: "smooth" });

    // Setup speech button
    const audioBtn = document.getElementById("listenAudioBtn");
    if (audioBtn) {
        audioBtn.onclick = () => {
            const speechText = `${data.risk_level}. ${data.summary}. ${t("precautionsTitle")} ${data.precautions.join(". ")}. ${data.when_to_seek_care}`;
            VoiceAssistant.toggleSpeech(speechText);
        };
    }
}

function resetChecker() {
    VoiceAssistant.stopSpeaking();
    hideAllCheckerSections();
    const input = document.getElementById("symptomInput");
    if (input) input.value = "";
    currentInitialSymptoms = "";
    currentFollowupQuestions = [];
    currentAssessmentResult = null;
    const inputSection = document.getElementById("symptomInputSection");
    if (inputSection) inputSection.classList.remove("d-none");
}

function hideAllCheckerSections() {
    ["emergencyAlertSection", "followupSection", "resultsSection"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add("d-none");
    });
}

function showCheckerLoading(show) {
    const loader = document.getElementById("checkerLoading");
    if (loader) {
        if (show) loader.classList.remove("d-none");
        else loader.classList.add("d-none");
    }
}
