/**
 * RuralCare AI - Patient Medical History Controller
 */

let historyRecords = [];

const MedicalHistory = {
    loadHistory: async function() {
        const container = document.getElementById("historyListContainer");
        const noHistoryEl = document.getElementById("noHistoryMessage");
        if (!container) return;

        container.innerHTML = `<div class="text-center p-4"><i class="fa-solid fa-spinner fa-spin fs-2 text-primary"></i></div>`;

        try {
            const resp = await fetch("/api/triage/history", {
                headers: Auth.getAuthHeader()
            });
            const data = await resp.json();
            historyRecords = data;

            container.innerHTML = "";

            if (!data || data.length === 0) {
                if (noHistoryEl) noHistoryEl.classList.remove("d-none");
                return;
            }

            if (noHistoryEl) noHistoryEl.classList.add("d-none");

            data.forEach((rec, idx) => {
                const dateStr = rec.created_at ? new Date(rec.created_at).toLocaleDateString(undefined, {
                    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                }) : "Recent";

                let badgeClass = "bg-success";
                if (rec.risk_level === "Emergency Risk") badgeClass = "bg-danger";
                else if (rec.risk_level === "Moderate Risk") badgeClass = "bg-warning text-dark";

                const card = document.createElement("div");
                card.className = "card mb-3 shadow-sm border-0 history-card";
                card.innerHTML = `
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2 flex-wrap">
                            <div>
                                <span class="badge ${badgeClass} fs-6 px-3 py-1 me-2">${rec.risk_level}</span>
                                <small class="text-muted"><i class="fa-regular fa-clock me-1"></i>${dateStr}</small>
                            </div>
                            <button class="btn btn-sm btn-outline-primary mt-2 mt-sm-0" onclick="MedicalHistory.openDetailModal(${rec.id})">
                                <i class="fa-solid fa-file-medical me-1"></i> ${t("viewDetailsBtn")}
                            </button>
                        </div>
                        <h6 class="fw-bold mb-1"><i class="fa-solid fa-notes-medical text-primary me-2"></i>${rec.primary_symptoms}</h6>
                        <p class="text-muted small mb-2">${rec.ai_summary || 'Triage completed.'}</p>
                        <div class="d-flex align-items-center gap-3 small text-secondary">
                            <div><i class="fa-solid fa-user-doctor me-1 text-primary"></i> ${rec.suggested_specialist || 'General Physician'}</div>
                            <div><i class="fa-solid fa-location-dot me-1 text-danger"></i> ${rec.location || 'Rural Region'}</div>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        } catch (err) {
            console.error("Error loading medical history:", err);
            container.innerHTML = `<div class="alert alert-danger">Failed to load medical history records.</div>`;
        }
    },

    openDetailModal: function(assessmentId) {
        const record = historyRecords.find(r => r.id === assessmentId);
        if (!record) return;

        document.getElementById("modalRecordSymptoms").innerText = record.primary_symptoms;
        document.getElementById("modalRecordDate").innerText = record.created_at || "Recent";
        
        const badge = document.getElementById("modalRecordRiskBadge");
        badge.className = "badge fs-6 px-3 py-2";
        if (record.risk_level === "Emergency Risk") badge.classList.add("bg-danger");
        else if (record.risk_level === "Moderate Risk") badge.classList.add("bg-warning", "text-dark");
        else badge.classList.add("bg-success");
        badge.innerText = record.risk_level;

        document.getElementById("modalRecordSummary").innerText = record.ai_summary || "No summary available.";
        document.getElementById("modalRecordSpecialist").innerText = record.suggested_specialist || "General Physician";

        // Causes
        const causesUl = document.getElementById("modalRecordCauses");
        causesUl.innerHTML = "";
        if (record.potential_causes && Array.isArray(record.potential_causes)) {
            record.potential_causes.forEach(c => {
                causesUl.innerHTML += `<li>${c}</li>`;
            });
        }

        // Precautions
        const precUl = document.getElementById("modalRecordPrecautions");
        precUl.innerHTML = "";
        if (record.home_care_precautions && Array.isArray(record.home_care_precautions)) {
            record.home_care_precautions.forEach(p => {
                precUl.innerHTML += `<li>${p}</li>`;
            });
        }

        document.getElementById("modalRecordSeekCare").innerText = record.when_to_seek_care || "Consult a doctor if symptoms worsen.";

        // Show modal
        const modalEl = document.getElementById("historyDetailModal");
        if (modalEl) {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        }
    },

    printCurrentSummary: function() {
        window.print();
    }
};
