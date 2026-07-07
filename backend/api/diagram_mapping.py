"""Diagram node to requirements mapping endpoints.

Requirement: 6.4 Diagram Mapping
- Requirements linked to diagrams
- Diagram nodes clickable retrieve from db

This module provides a simple endpoint that maps a diagram element/node
(identified by DiagramElement.element_id) to its source requirement(s).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.user import User
from backend.models.requirement import Requirement
from backend.models.diagram import DiagramElement, Diagram
from backend.models.project import Project
from backend.utils.security import get_current_active_user
from backend.config.database import get_db
from backend.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/diagram/{diagram_id}/elements/{element_id}/requirements",
    summary="Get requirements linked to a diagram element (node)",
)
async def get_requirements_for_diagram_element(
    diagram_id: str,
    element_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return requirements linked to a specific diagram node.

    Uses DiagramElement.source_req_id to fetch Requirement rows.
    """
    try:
        # Verify diagram exists + user has access to its project
        stmt_diagram = select(Diagram).where(Diagram.diagram_id == diagram_id)
        diagram_result = await db.execute(stmt_diagram)
        diagram = diagram_result.scalar_one_or_none()
        if not diagram:
            raise HTTPException(status_code=404, detail="Diagram not found")

        stmt_project = select(Project).where(Project.project_id == diagram.project_id)
        project_result = await db.execute(stmt_project)
        project = project_result.scalar_one_or_none()
        if not project or project.owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Find the diagram element
        stmt_element = select(DiagramElement).where(
            DiagramElement.diagram_id == diagram_id,
            DiagramElement.element_id == element_id,
        )
        element_result = await db.execute(stmt_element)
        element = element_result.scalar_one_or_none()
        if not element:
            raise HTTPException(status_code=404, detail="Diagram element not found")

        if not element.source_req_id:
            return {"requirements": []}

        # Fetch requirement
        stmt_req = select(Requirement).where(Requirement.req_id == element.source_req_id)
        req_result = await db.execute(stmt_req)
        req = req_result.scalar_one_or_none()
        if not req:
            return {"requirements": []}

        # Return a compatible shape for the frontend Traceability table.
        return {
            "diagram": {
                "diagram_id": diagram_id,
                "element_id": element_id,
                "element_type": element.element_type,
                "element_name": element.element_name,
            },
            "requirements": [
                {
                    "req_id": req.req_id,
                    "identifier": req.req_identifier or f"REQ-{req.sequence_order + 1:03d}",
                    "text": req.current_text or req.original_text,
                    # validation_status/complexity/visual_elements are computed in traceability API.
                    # Here we return minimal fields and let the frontend compute/handle missing ones.
                    "validation_status": getattr(req, "validation_status", "passed"),
                    "visual_elements": [],
                    "complexity": "Medium",
                }
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to get requirements for diagram element",
            extra={"diagram_id": diagram_id, "element_id": element_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve linked requirements",
        )

