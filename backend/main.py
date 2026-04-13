import uvicorn
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from config.database import engine, Base
from api.analysis import router as analysis_router
from api.visualization import router as visualization_router
from api.users import router as users_router
from api.auth import router as auth_router
from api.validation import router as validation_router
from api.reports import router as reports_router
from utils.security import verify_token
from models.user import User, UserRole
# Import all models so SQLAlchemy registers them with Base.metadata
from models import (
    PasswordResetToken, SystemLog,
    Project, RequirementDocument, Requirement,
    ValidationSession, Defect, AIPromptLog,
    Diagram, DiagramElement, ProjectMetrics,
    TraceabilityMatrix, TraceabilityNote,
    ReviewAudit, ExportReport,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])
app.include_router(visualization_router, prefix="/api/visualization", tags=["visualization"])
app.include_router(validation_router, tags=["validation"])
app.include_router(reports_router, tags=["reports"])


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
