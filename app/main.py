import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.seed import seed_database
from app.routers import auth, triage, doctors, emergency

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ruralcare")

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="RuralCare AI – Smart Healthcare Access Platform",
    description="AI-powered rural healthcare access platform with multi-lingual voice triage, emergency safety layer, doctor finder & history tracking.",
    version="1.0.0"
)

# Enable CORS for local testing & development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
static_path = BASE_DIR / "static"
templates_path = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

# Include API Routers
app.include_router(auth.router)
app.include_router(triage.router)
app.include_router(doctors.router)
app.include_router(emergency.router)

@app.on_event("startup")
def startup_event():
    logger.info("Initializing database and seeding sample data...")
    init_db()
    seed_database()
    logger.info("RuralCare AI server startup complete.")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Serve the primary Single Page Application interface."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RuralCare AI",
        "version": "1.0.0"
    }
