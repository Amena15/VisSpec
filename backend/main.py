import uvicorn
from datetime import datetime, timezone
from contextlib import asynccontextmanager


import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Ensure backend/ package imports work when launched from repo root
BACKEND_ROOT = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATIC_DIR = BACKEND_ROOT / "static"

from backend.core.config import settings
from backend.config.database import engine, Base
from backend.core.task_queue import task_queue

# Import routers
from backend.api.analysis import router as analysis_router
from backend.api.auth import router as auth_router
from backend.api.documents import router as documents_router
from backend.api.diagrams import router as diagrams_router
from backend.api.diagram_mapping import router as diagram_mapping_router
from backend.api.uml_diagrams import router as ieee_diagrams_router

from backend.api.projects import router as projects_router
from backend.api.traceability import router as traceability_router
from backend.api.users import router as users_router
from backend.api.validation import router as validation_router
from backend.api.visualization import router as visualization_router
from backend.api.reports import router as reports_router
from backend.api.processing import router as processing_router
from backend.api.supervisor import router as supervisor_router
from backend.api.notifications import router as notifications_router

# Import all models so SQLAlchemy registers them with Base.metadata
from backend.models import (
    PasswordResetToken, SystemLog,
    Project, RequirementDocument, Requirement,
    ValidationSession, Defect, AIPromptLog,
    Diagram, DiagramElement, ProjectMetrics,
    TraceabilityMatrix, TraceabilityNote,
    ReviewAudit, ExportReport,
    Notification,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Create database tables (sync, acceptable for development)
    from sqlalchemy import create_engine

    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql+asyncpg://"):
        sync_db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgresql://"):
        sync_db_url = db_url
    elif db_url.startswith("postgres+asyncpg://"):
        sync_db_url = db_url.replace("postgres+asyncpg://", "postgresql://", 1)
    else:
        sync_db_url = db_url

    sync_engine = create_engine(sync_db_url)
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()

    # Start background task processor
    await task_queue.start_processor()

    yield

    # --- Shutdown ---
    await task_queue.stop_processor(timeout=5.0)
    await engine.dispose()  # close async engine connections


app = FastAPI(
    title="VisSpec - Visual Specification System",
    description="AI-powered system for converting textual requirements into visual specifications",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # For development only; restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, tags=["auth"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(projects_router, tags=["projects"])
app.include_router(documents_router, tags=["documents"])
app.include_router(traceability_router, prefix="/api/traceability", tags=["traceability"])
app.include_router(processing_router, prefix="/api/processing", tags=["processing"])
app.include_router(analysis_router, tags=["analysis"])
app.include_router(supervisor_router, prefix="/api/supervisor", tags=["supervisor"])
app.include_router(visualization_router, prefix="/api/visualization", tags=["visualization"])
app.include_router(diagrams_router, prefix="/api/diagrams", tags=["diagrams"])
app.include_router(diagram_mapping_router, prefix="/api/diagrams", tags=["diagram-mapping"])
app.include_router(ieee_diagrams_router, prefix="/api/ieee-diagrams", tags=["ieee-diagrams"])

app.include_router(validation_router, tags=["validation"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["notifications"])



@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }

@app.get("/test-direct")
async def test_direct():
    return {"message": "Direct route works"}

@app.get("/")
def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    return {"message": "VisSpec API is running", "version": "1.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health", "test-direct")):
        raise HTTPException(status_code=404, detail="Not Found")

    requested_file = STATIC_DIR / full_path
    if requested_file.is_file():
        return FileResponse(requested_file)

    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Not Found")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

    