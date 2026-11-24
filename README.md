# 🏥 RuralCare AI – Smart Healthcare Access Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python)](https://www.python.org/)
[![Database-SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg?logo=sqlite)](https://www.sqlite.org/)
[![Maps-OpenStreetMap](https://img.shields.io/badge/Maps-OpenStreetMap%20%2B%20Leaflet-7EBC6F.svg?logo=openstreetmap)](https://leafletjs.com/)
[![Web-Speech-API](https://img.shields.io/badge/Voice-Web%20Speech%20API-FF6F00.svg)](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
[![Tests-Passed](https://img.shields.io/badge/Tests-24%2F24%20Passed%20(100%25)-success.svg)](file:///tests/run_tests.py)

> **RuralCare AI** is an AI-powered healthcare access and triage platform designed specifically for rural communities. It overcomes severe rural healthcare bottlenecks: limited doctors, language barriers, low medical awareness, and delayed identification of serious emergencies.

---

## 🌟 Key Features

### 1. 🗣️ Multilingual Voice Assistant (5 Regional Languages)
- Full voice input (**Speech-to-Text**) and voice readout (**Text-to-Speech**) via Web Speech API.
- Native regional locale support:
  - **English (`en-IN`)**
  - **ಕನ್ನಡ - Kannada (`kn-IN`)**
  - **हिन्दी - Hindi (`hi-IN`)**
  - **தமிழ் - Tamil (`ta-IN`)**
  - **తెలుగు - Telugu (`te-IN`)**
- High-contrast, large touch-friendly buttons designed for low-literacy users and elderly patients.

### 2. 🚨 Deterministic Rule-Based Emergency Safety Layer
- **Never relies solely on an LLM for life-or-death emergencies.**
- Deterministic regex and clinical rule engine evaluates incoming symptoms **instantly** before any LLM inference.
- Detects acute emergencies across all 5 languages and transliterated romanized forms:
  - **Acute Coronary Syndrome / Heart Attack** (chest pain, left arm radiation, sweating)
  - **Respiratory Failure / Suffocation** (gasping for air, cyanosis / blue lips)
  - **Acute Stroke / FAST Signs** (facial drooping, slurred speech, one-sided weakness)
  - **Snakebite & Envenomation** (snake bite, scorpion sting, pesticide ingestion)
  - **Severe Uncontrolled Hemorrhage & Trauma**
  - **Unresponsiveness / Prolonged Seizure**
  - **Anaphylactic Shock**
- **Zero-Delay Action Screen**: Instantly flashes red alert, provides clear first-aid steps in native language, and triggers **1-tap 108 Ambulance Dispatch**.

### 3. 🧠 AI Symptom Checker & Clinical Triage
- Guided 2-step conversational assessment:
  1. Primary symptom capture (voice or text).
  2. Targeted, clinically relevant follow-up questions (duration, severity, red-flag symptoms).
- **Risk Level Classification**:
  - 🟢 **Low Risk** (Home care, hydration, rest, monitoring)
  - 🟡 **Moderate Risk** (Visit Primary Health Center within 24-48 hours)
  - 🔴 **Emergency Risk** (Immediate emergency medical care)
- **Dual Engine Architecture**:
  - Connects to **Google Gemini API** (`gemini-2.5-flash`) when configured.
  - Features an intelligent, comprehensive **Heuristic Clinical Expert Engine fallback** that ensures 100% functionality even when offline or without an API key.
- **Strict Non-Diagnostic Disclaimer**: Never claims to diagnose. Always explains potential conditions as topics to discuss with a licensed doctor.

### 4. 🗺️ Rural Doctor & Health Facility Finder (Leaflet.js + OpenStreetMap)
- Interactive OpenStreetMap showing Primary Health Centers (PHCs), Community Health Centers (CHCs), Sub-District Hospitals, and local doctors.
- Real-time GPS location detection (`HTML5 Geolocation API`) and distance calculation using the **Haversine formula**.
- Direct `tel:` call button to connect with the hospital/doctor.
- 1-click **Get Directions** to navigate using Google Maps or OpenStreetMap.
- Filters by District, Doctor Specialization, Facility Type, and Emergency Capable status.

### 5. 📋 Patient Registration & Medical History
- Simple, mobile-friendly registration collecting: Name, Age, Gender, Village, District, State, Phone, Blood Group, and Existing Conditions (BP/Sugar/Allergies).
- Secure password hashing using salted **PBKDF2-HMAC-SHA256** and stateless **JWT authentication**.
- Saves every health assessment timeline with date, symptoms, risk level, specialist advice, and safe home remedies.
- Printable Health Summary card for patients to carry to the clinic.

### 6. 🆘 24x7 Emergency Hub
- Direct access to national emergency lifelines:
  - **108**: Toll-free emergency ambulance across rural & urban India.
  - **104**: 24x7 government medical advice, ASHA worker support, tele-triage.
  - **112**: All-in-One national emergency hotline.
  - **1800-116-117**: National Poison Information Center.
- Curated step-by-step first aid guides for common rural emergencies (Snakebite protocol, Heart attack, Severe bleeding, Heatstroke, Choking).

---

## 🏗️ System Architecture

```
                                    +-----------------------------------------+
                                    |         User (Rural Patient)            |
                                    | Voice (STT) / Touch / Text in 5 Langs   |
                                    +--------------------+--------------------+
                                                         |
                                                         v
                                    +-----------------------------------------+
                                    |     Responsive Frontend Single Page App |
                                    |  HTML5 + CSS3 + Bootstrap 5.3 + Vanilla |
                                    |  Web Speech API (STT & TTS)             |
                                    |  Leaflet.js (OpenStreetMap)             |
                                    +--------------------+--------------------+
                                                         |  JSON / REST API
                                                         v
                                    +-----------------------------------------+
                                    |       FastAPI Backend Application       |
                                    |  (Async, Typed, High Performance)       |
                                    +---------+--------------------+----------+
                                              |                    |
                 +----------------------------+                    +---------------------------+
                 v                                                                             v
+----------------------------------+                                        +----------------------------------+
|  Tier 1: Emergency Safety Layer  |                                        |  Tier 2: AI Triage & Assessment  |
|  Deterministic Regex Rules       |                                        |  - Google Gemini 2.5 Flash API   |
|  - Cardiac, Stroke, Snakebite,   |                                        |  - Heuristic Clinical Fallback   |
|    Hemorrhage, Anaphylaxis       |                                        |  - Risk Classification (L/M/E)   |
|  - Instant 108 Dispatch Trigger  |                                        |  - Follow-up Question Engine     |
+----------------------------------+                                        +----------------------------------+
                 |                                                                             |
                 +----------------------------+                    +---------------------------+
                                              v                    v
                                    +-----------------------------------------+
                                    |       SQLite Database (ruralcare.db)    |
                                    |  - patients                             |
                                    |  - assessments (medical history)        |
                                    |  - doctors & facilities (PHCs/CHCs)     |
                                    |  - emergency_logs                       |
                                    +-----------------------------------------+
```

---

## 🛠️ Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Backend** | Python 3.10+, FastAPI, Uvicorn | High-performance, async, typed REST API with automatic OpenAPI interactive docs |
| **Database** | SQLite 3 (`sqlite3` standard library) | Zero configuration, ACID-compliant, self-contained, pre-seeded with rural health data |
| **AI / Triage** | Google Gemini API + Heuristic Clinical Knowledge Engine | Dual architecture guarantees 100% reliability even without internet or API key |
| **Safety Layer** | Deterministic Regex & Clinical Red-Flag Rules | Eliminates LLM hallucination and latency for critical emergency symptoms |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3 | Lightweight, zero-build-step, ultra-fast load time on low-bandwidth 2G/3G networks |
| **Maps** | Leaflet.js + OpenStreetMap | Free, open-source mapping without proprietary API key barriers |
| **Voice** | HTML5 Web Speech API | Native speech recognition and synthesis for Indian accents and regional languages |
| **Security** | Salted PBKDF2-HMAC-SHA256 + PyJWT | Secure password hashing and stateless token authentication |

---

## 🚀 Quickstart & Installation Instructions

### Prerequisites
- Python 3.10 or higher installed on your system.
- Standard modern web browser (Google Chrome, Microsoft Edge, or Android Browser recommended for Web Speech API).

### 1. Clone or Open Project Directory
```powershell
cd "c:\Users\yynai\OneDrive\Desktop\medical difficulties"
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. (Optional) Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
*(Optional: Add your `GEMINI_API_KEY`. If not supplied, RuralCare AI automatically runs using its built-in heuristic clinical expert engine).*

### 4. Run the Automated Verification Suite
Verify all 24 unit, safety, and API tests:
```powershell
python tests/run_tests.py
```
*(Expected output: `All 24 RuralCare AI verification tests PASSED with 100% success!`)*

### 5. Launch the Web Application
```powershell
python run.py
```
Or with Uvicorn directly:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Open the Application
Open your browser and navigate to:
- **Web App**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Redoc API Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 👥 Demo Accounts (Pre-Seeded)

| Patient Name | Mobile Number | Password | Language | Village & District | Pre-existing Condition |
|---|---|---|---|---|---|
| **Basavaraju M.** | `9876543210` | `password123` | Kannada (`kn`) | Kailancha, Ramanagara | Hypertension (High BP) |
| **Sunita Devi** | `9876500001` | `password123` | Hindi (`hi`) | Harohalli, Ramanagara | None |
| **Murugesan K.** | `9876500002` | `password123` | Tamil (`ta`) | Mathigiri, Krishnagiri | Type 2 Diabetes |

*Note: Guest users can also use the Symptom Checker, Doctor Finder, and Emergency Hub without logging in.*

---

## 📡 API Endpoints Reference

### 🔐 Authentication (`/api/auth`)
- `POST /api/auth/register` - Register a new patient.
- `POST /api/auth/login` - Authenticate via phone and password.
- `GET /api/auth/me` - Fetch profile of currently authenticated patient.

### 🩺 Symptom Checker & Triage (`/api/triage`)
- `POST /api/triage/assess` - Evaluates initial symptoms against rule-based emergency safety layer. If emergency, returns immediate 108 protocol. If non-emergency, returns smart follow-up questions.
- `POST /api/triage/followup` - Analyzes follow-up answers and returns final risk classification (Low, Moderate, Emergency), recommended doctor specialist, possible causes, precautions, and care timeline.
- `GET /api/triage/history` - Fetches historical health assessments for the patient.
- `GET /api/triage/history/{id}` - Fetches detailed assessment breakdown by ID.

### 🏥 Doctor & Facility Finder (`/api/doctors`)
- `GET /api/doctors/nearby?lat={lat}&lon={lon}&district={dist}&specialization={spec}&facility_type={type}&emergency_only={bool}` - Query doctors with GPS distance calculation and multi-criteria filters.
- `GET /api/doctors/districts` - List all covered districts.
- `GET /api/doctors/specializations` - List available doctor specializations.
- `GET /api/doctors/{id}` - Retrieve details of a specific healthcare facility.

### 🚨 Emergency & SOS (`/api/emergency`)
- `GET /api/emergency/helplines` - Returns emergency numbers (108, 112, 104, 181, 1098, Poison Control).
- `GET /api/emergency/first-aid` - Returns multilingual step-by-step first aid guides.
- `POST /api/emergency/sos` - Logs manual SOS trigger and dispatches emergency protocol.

---

## 🧪 Verification & Testing Results

All 24 automated tests executed via `tests/run_tests.py`:
- ✅ `test_emergency_rule_cardiac_english`: PASSED
- ✅ `test_emergency_rule_snakebite_kannada`: PASSED
- ✅ `test_emergency_rule_respiratory_hindi`: PASSED
- ✅ `test_emergency_rule_stroke_tamil`: PASSED
- ✅ `test_emergency_rule_unresponsive_telugu`: PASSED
- ✅ `test_non_emergency_mild_symptom`: PASSED
- ✅ `test_followup_questions_generation`: PASSED
- ✅ `test_heuristic_triage_evaluation`: PASSED
- ✅ `test_password_hashing`: PASSED
- ✅ `test_jwt_token`: PASSED
- ✅ `test_demo_patient_exists`: PASSED
- ✅ `test_haversine_distance`: PASSED
- ✅ `test_get_doctors_all`: PASSED
- ✅ `test_get_doctors_district_filter`: PASSED
- ✅ `test_get_doctors_emergency_capable`: PASSED
- ✅ `test_get_doctors_distance_sorting`: PASSED
- ✅ `test_health_check`: PASSED
- ✅ `test_homepage_serves_html`: PASSED
- ✅ `test_auth_flow`: PASSED
- ✅ `test_triage_emergency_route`: PASSED
- ✅ `test_triage_non_emergency_and_followup`: PASSED
- ✅ `test_doctors_routes`: PASSED
- ✅ `test_emergency_routes`: PASSED
- ✅ `test_patient_history`: PASSED

---

## ⚖️ Ethical & Medical Disclaimer
**RuralCare AI** is an assistive triage and health accessibility guidance tool designed to help rural patients evaluate symptom urgency and connect with nearby verified healthcare providers. It is **not** a diagnostic device and **does not** replace qualified medical doctors or emergency healthcare services.
