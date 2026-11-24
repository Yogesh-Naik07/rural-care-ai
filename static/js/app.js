/**
 * RuralCare AI - Main Application & State Controller
 */

const Auth = {
    getToken: function() {
        return localStorage.getItem("ruralcare_token");
    },
    getPatient: function() {
        const data = localStorage.getItem("ruralcare_patient");
        return data ? JSON.parse(data) : null;
    },
    getAuthHeader: function() {
        const token = this.getToken();
        return token ? { "Authorization": `Bearer ${token}` } : {};
    },
    saveSession: function(token, patient) {
        localStorage.setItem("ruralcare_token", token);
        localStorage.setItem("ruralcare_patient", JSON.stringify(patient));
        this.updateAuthUI();
    },
    logout: function() {
        localStorage.removeItem("ruralcare_token");
        localStorage.removeItem("ruralcare_patient");
        this.updateAuthUI();
        App.navigate("home");
    },
    updateAuthUI: function() {
        const patient = this.getPatient();
        const guestNav = document.getElementById("guestNavButtons");
        const userNav = document.getElementById("userNavButtons");
        const userNameLabel = document.getElementById("currentUserName");

        if (patient) {
            if (guestNav) guestNav.classList.add("d-none");
            if (userNav) userNav.classList.remove("d-none");
            if (userNameLabel) userNameLabel.innerText = patient.name;
        } else {
            if (guestNav) guestNav.classList.remove("d-none");
            if (userNav) userNav.classList.add("d-none");
            if (userNameLabel) userNameLabel.innerText = t("guestUser");
        }
    }
};

const App = {
    currentTab: "home",

    init: function() {
        // Set language
        const savedLang = localStorage.getItem("ruralcare_lang") || "en";
        setLanguage(savedLang);

        // Update auth UI
        Auth.updateAuthUI();

        // Load emergency guides
        this.loadFirstAidGuides();

        // Listen for hash changes
        window.addEventListener("hashchange", () => {
            const hash = window.location.hash.replace("#", "") || "home";
            this.navigate(hash);
        });

        // Initialize to hash or home
        const initialHash = window.location.hash.replace("#", "") || "home";
        this.navigate(initialHash);

        // Register form submit handlers
        this.bindAuthForms();
    },

    navigate: function(tabName) {
        this.currentTab = tabName;
        window.location.hash = tabName;

        // Hide all views
        document.querySelectorAll(".app-view").forEach(v => v.classList.add("d-none"));

        // Show target view
        const targetView = document.getElementById(`view-${tabName}`);
        if (targetView) {
            targetView.classList.remove("d-none");
            window.scrollTo({ top: 0, behavior: "smooth" });
        }

        // Update active class on nav links
        document.querySelectorAll(".nav-link").forEach(link => {
            if (link.getAttribute("href") === `#${tabName}`) {
                link.classList.add("active");
            } else {
                link.classList.remove("active");
            }
        });

        // Trigger view-specific inits
        if (tabName === "doctors") {
            DoctorFinder.init();
        } else if (tabName === "history") {
            MedicalHistory.loadHistory();
        }
    },

    loadFirstAidGuides: async function() {
        const container = document.getElementById("firstAidContainer");
        if (!container) return;

        try {
            const resp = await fetch("/api/emergency/first-aid");
            const guides = await resp.json();

            container.innerHTML = "";
            guides.forEach(g => {
                const title = (currentLanguage !== "en" && g.local_titles && g.local_titles[currentLanguage])
                    ? g.local_titles[currentLanguage]
                    : g.title;

                let stepsHtml = "";
                g.action_steps.forEach((s, idx) => {
                    stepsHtml += `<li class="mb-2"><span class="badge bg-danger rounded-circle me-1">${idx + 1}</span> ${s}</li>`;
                });

                const col = document.createElement("div");
                col.className = "col-md-6 col-lg-4 mb-4";
                col.innerHTML = `
                    <div class="card h-100 shadow-sm border-0 first-aid-card">
                        <div class="card-header bg-danger text-white fw-bold d-flex align-items-center">
                            <i class="fa-solid ${g.icon} me-2 fs-5"></i> ${title}
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled mb-0 small">
                                ${stepsHtml}
                            </ul>
                        </div>
                    </div>
                `;
                container.appendChild(col);
            });
        } catch (e) {
            console.error("Error loading first aid guides:", e);
        }
    },

    triggerEmergencySOS: async function() {
        if (!confirm("Are you sure you want to trigger Emergency SOS (108 Ambulance Alert)?")) {
            return;
        }

        const patient = Auth.getPatient();
        const payload = {
            patient_id: patient ? patient.id : null,
            patient_name: patient ? patient.name : "Emergency Caller",
            phone: patient ? patient.phone : "Unknown",
            location: patient ? (patient.village + ", " + patient.district) : "Rural Location",
            trigger_reason: "Manual Emergency SOS Button"
        };

        try {
            await fetch("/api/emergency/sos", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        } catch (e) {
            console.warn("SOS logged locally:", e);
        }

        // Direct call initiation
        window.location.href = "tel:108";
    },

    bindAuthForms: function() {
        // Login form
        const loginForm = document.getElementById("loginForm");
        if (loginForm) {
            loginForm.onsubmit = async (e) => {
                e.preventDefault();
                const phone = document.getElementById("loginPhone").value.trim();
                const password = document.getElementById("loginPassword").value;
                const errBox = document.getElementById("loginError");

                try {
                    const resp = await fetch("/api/auth/login", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ phone, password })
                    });
                    const data = await resp.json();

                    if (!resp.ok) {
                        if (errBox) {
                            errBox.innerText = data.detail || "Login failed.";
                            errBox.classList.remove("d-none");
                        }
                        return;
                    }

                    Auth.saveSession(data.access_token, data.patient);
                    const modalEl = document.getElementById("authModal");
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    loginForm.reset();
                    if (errBox) errBox.classList.add("d-none");
                } catch (err) {
                    console.error("Login error:", err);
                    if (errBox) {
                        errBox.innerText = "Network error. Please try again.";
                        errBox.classList.remove("d-none");
                    }
                }
            };
        }

        // Register form
        const registerForm = document.getElementById("registerForm");
        if (registerForm) {
            registerForm.onsubmit = async (e) => {
                e.preventDefault();
                const payload = {
                    name: document.getElementById("regName").value.trim(),
                    age: parseInt(document.getElementById("regAge").value),
                    gender: document.getElementById("regGender").value,
                    village: document.getElementById("regVillage").value.trim(),
                    district: document.getElementById("regDistrict").value.trim(),
                    state: document.getElementById("regState").value.trim(),
                    phone: document.getElementById("regPhone").value.trim(),
                    password: document.getElementById("regPassword").value,
                    blood_group: document.getElementById("regBlood").value.trim(),
                    allergies: document.getElementById("regAllergies").value.trim(),
                    chronic_conditions: document.getElementById("regChronic").value.trim(),
                    preferred_language: currentLanguage
                };

                const errBox = document.getElementById("regError");

                try {
                    const resp = await fetch("/api/auth/register", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                    const data = await resp.json();

                    if (!resp.ok) {
                        if (errBox) {
                            errBox.innerText = data.detail || "Registration failed.";
                            errBox.classList.remove("d-none");
                        }
                        return;
                    }

                    Auth.saveSession(data.access_token, data.patient);
                    const modalEl = document.getElementById("authModal");
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if (modal) modal.hide();
                    registerForm.reset();
                    if (errBox) errBox.classList.add("d-none");
                } catch (err) {
                    console.error("Register error:", err);
                    if (errBox) {
                        errBox.innerText = "Network error. Please try again.";
                        errBox.classList.remove("d-none");
                    }
                }
            };
        }
    },

    fillDemoUser: function(phone, pw) {
        const phoneInput = document.getElementById("loginPhone");
        const pwInput = document.getElementById("loginPassword");
        if (phoneInput && pwInput) {
            phoneInput.value = phone;
            pwInput.value = pw;
        }
    }
};

window.addEventListener("DOMContentLoaded", () => {
    App.init();
});
