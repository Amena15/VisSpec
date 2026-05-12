import uvicorn
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from config.database import engine, Base
from api.analysis import router as analysis_router
from api.auth import router as auth_router
from api.documents import router as documents_router
from api.diagrams import router as diagrams_router
from api.projects import router as projects_router
from api.traceability import router as traceability_router
from api.users import router as users_router
from api.validation import router as validation_router
from api.visualization import router as visualization_router
from api.reports import router as reports_router
from api.processing import router as processing_router
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
app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(traceability_router)
app.include_router(processing_router)
app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])
app.include_router(visualization_router, prefix="/api/visualization", tags=["visualization"])
app.include_router(diagrams_router, prefix="/api/diagrams", tags=["diagrams"])
app.include_router(validation_router, tags=["validation"])
app.include_router(reports_router, tags=["reports"])
app.include_router(processing_router, prefix="/api", tags=["processing"])


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


# Test endpoint to bypass authentication for document upload testing
@app.post("/test-upload")
async def test_document_upload(
    project_id: str,
    file: UploadFile = File(...),
):
    """
    Test document upload endpoint without authentication.
    Only for development testing.
    """
    try:
        # Import required modules
        import uuid
        from datetime import datetime, timezone
        from services.document.parser import DocumentParser
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        filename = file.filename or "test_file"
        
        # Parse document
        parser = DocumentParser()
        parse_result = parser.parse(file_content, filename)
        
        if "error" in parse_result:
            return {
                "success": False,
                "error": parse_result["error"],
                "filename": filename,
                "file_size": file_size
            }
        
        return {
            "success": True,
            "filename": filename,
            "file_size": file_size,
            "parse_result": parse_result,
            "message": "Document parsed successfully"
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Document upload test failed"
        }


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
