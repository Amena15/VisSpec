"""Report export API routes - Module 6: Reporting & Dashboard
Enhanced with input validation, access control, and error handling.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_validator
import io
import logging
import traceback

from backend.models.user import User
from backend.utils.security import get_current_active_user
from backend.services.report.export_service import ReportExportService
from backend.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["reports"])


# Pydantic request models for validation (SECURITY)
class ReportExportRequest(BaseModel):
    """Validated report export request"""
    project_name: Optional[str] = "Untitled Project"
    project_id: Optional[str] = None
    analysis_data: Optional[Dict[str, Any]] = {}
    diagrams: Optional[List[Dict[str, Any]]] = []
    metrics: Optional[Dict[str, Any]] = {}
    traceability: Optional[List[Dict[str, Any]]] = []
    report_type: Optional[str] = "full"
    
    @field_validator('project_name')
    @classmethod
    def validate_project_name(cls, v):
        if v and len(v) > 500:
            raise ValueError('Project name exceeds maximum length of 500 characters')
        return v
    
    @field_validator('report_type')
    @classmethod
    def validate_report_type(cls, v):
        valid_types = ["full", "summary", "supervisor"]
        if v and v not in valid_types:
            raise ValueError(f'Report type must be one of {valid_types}')
        return v


@router.post("/export")
async def export_report(
    request: ReportExportRequest,
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """
    Generate a PDF report with analysis results, diagrams, and metrics.
    Supports full, summary, and supervisor report types.
    
    Enhanced with:
    - Input validation (Pydantic request model)
    - Error handling with structured logging
    - Generic error messages to client (no detail leakage)
    """
    try:
        logger.info(
            f"Report export initiated",
            extra={
                "user_id": current_user.user_id,
                "project_id": request.project_id,
                "report_type": request.report_type,
            }
        )
        
        # Input validation passed by Pydantic
        service = ReportExportService()

        project_name = request.project_name or "Untitled Project"
        analysis_data = request.analysis_data or {}
        diagrams = request.diagrams or []
        metrics = request.metrics or {}
        traceability = request.traceability or []
        report_type = request.report_type or "full"

        # Sanitize project name for filename (security)
        safe_filename = "".join(
            c if c.isalnum() or c in (' ', '-', '_') else '_' 
            for c in project_name
        ).strip()

        pdf_bytes = service.generate_report(
            project_name=project_name,
            analysis_data=analysis_data,
            diagrams=diagrams,
            metrics=metrics,
            traceability=traceability,
            report_type=report_type,
        )

        logger.info(
            f"Report generated successfully",
            extra={
                "user_id": current_user.user_id,
                "report_type": report_type,
                "pdf_size": len(pdf_bytes),
            }
        )

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="vispec_report_{safe_filename}.pdf"',
            },
        )
    except ValueError as e:
        # Input validation errors
        logger.warning(
            f"Report generation validation error",
            extra={"user_id": current_user.user_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report parameters. Please check your input."
        )
    except Exception as e:
        # General errors - log with context but return generic message
        logger.exception(
            f"Report generation failed",
            extra={
                "user_id": current_user.user_id,
                "project_id": request.project_id,
                "report_type": request.report_type,
                "error": str(e),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report generation failed. Please try again or contact support."
        )