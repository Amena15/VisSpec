"""Report export API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from backend.models.user import User
from backend.utils.security import get_current_active_user
from backend.services.report.export_service import ReportExportService
from backend.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["reports"])


@router.post("/export")
async def export_report(
    request: dict,
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate a PDF report with analysis results, diagrams, and metrics.
    Supports full, summary, and supervisor report types.
    """
    try:
        service = ReportExportService()

        project_name = request.get("project_name", "Untitled Project")
        analysis_data = request.get("analysis_data", {})
        diagrams = request.get("diagrams", [])
        metrics = request.get("metrics", {})
        traceability = request.get("traceability", [])
        report_type = request.get("report_type", "full")

        pdf_bytes = service.generate_report(
            project_name=project_name,
            analysis_data=analysis_data,
            diagrams=diagrams,
            metrics=metrics,
            traceability=traceability,
            report_type=report_type,
        )

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="vispec_report_{project_name.replace(" ", "_")}.pdf"',
            },
        )
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )