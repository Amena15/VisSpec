import uvicorn
from datetime import datetime
from contextlib import asynccontextmanager

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend/ package imports work when launched from repo root
BACKEND_ROOT = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.core.config import settings
from backend.config.database import engine, Base


# DB driver sanity check is handled in config/database.py (async engine setup)
# Avoid failing startup if env still uses a sync driver; we auto-upgrade when possible.
from backend.api.analysis import router as analysis_router
from backend.api.auth import router as auth_router
from backend.api.documents import router as documents_router
from backend.api.diagrams import router as diagrams_router
from backend.api.ieee_diagrams import router as ieee_diagrams_router
from backend.api.projects import router as projects_router
from backend.api.traceability import router as traceability_router
from backend.api.users import router as users_router
from backend.api.validation import router as validation_router
from backend.api.visualization import router as visualization_router
from backend.api.reports import router as reports_router
from backend.api.processing import router as processing_router
from backend.api.supervisor import router as supervisor_router
from backend.api.notifications import router as notifications_router


from models.user import User, UserRole
# Import all models so SQLAlchemy registers them with Base.metadata
from models import (
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

    # Startup
    # Using sync engine for table creation 
    from sqlalchemy import create_engine

    db_url = settings.DATABASE_URL
    # Convert asyncpg URL -> sync URL for metadata creation
    if db_url.startswith("postgresql+asyncpg://"):
        sync_db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgresql://"):
        # Already sync URL
        sync_db_url = db_url
    elif db_url.startswith("postgres+asyncpg://"):
        sync_db_url = db_url.replace("postgres+asyncpg://", "postgresql://", 1)
    else:
        # Last resort: keep original and let SQLAlchemy raise if invalid
        sync_db_url = db_url


    sync_engine = create_engine(sync_db_url)
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()
    yield
    # Shutdown


app = FastAPI(
    title="VisSpec - Visual Specification System",
    description="AI-powered system for converting textual requirements into visual specifications",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3006",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3006",
        "http://127.0.0.1:5173",
        "*"  # Fallback for any other origins
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers with proper prefixes (avoiding duplicate prefixes)
app.include_router(auth_router, tags=["auth"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(projects_router, tags=["projects"])  # Already has prefix
app.include_router(documents_router, tags=["documents"])  # Already has prefix
app.include_router(traceability_router, prefix="/api/traceability", tags=["traceability"])
app.include_router(processing_router, prefix="/api/processing", tags=["processing"])
app.include_router(analysis_router, tags=["analysis"])  # Already has prefix

# Supervisor (Module 6)
# Ensure the supervisor router is mounted so /api/supervisor/* routes exist.
app.include_router(supervisor_router, prefix="/api/supervisor", tags=["supervisor"])

app.include_router(visualization_router, prefix="/api/visualization", tags=["visualization"])
app.include_router(diagrams_router, prefix="/api/diagrams", tags=["diagrams"])
app.include_router(ieee_diagrams_router, prefix="/api/ieee-diagrams", tags=["ieee-diagrams"])
app.include_router(validation_router, tags=["validation"])  # Already has prefix
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["notifications"])




# Health check endpoint

@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


# Root endpoint
@app.get("/")
def root():
    return {"message": "VisSpec API is running", "version": "1.0.0", "timestamp": datetime.utcnow().isoformat()}


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
