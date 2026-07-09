"""Traceability API routes for REQ_18 and UC-09 implementation."""
import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.models.user import User
from backend.models.project import Project
from backend.models.requirement import Requirement
from backend.models.document import RequirementDocument
from backend.models.validation import Defect
from backend.models.traceability import TraceabilityNote
from backend.utils.security import get_current_active_user
from backend.utils.complexity import determine_requirement_complexity
from backend.config.database import get_db
from backend.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class TraceabilityItem(BaseModel):
    """Single traceability item response."""
    req_id: str
    doc_id: Optional[str] = None
    identifier: str
    semantic_id: Optional[str] = None
    text: str
    validation_status: str  # passed, warning, failed, pending
    visual_elements: List[str] = []
    complexity: str  # High, Medium, Low
    note: Optional[dict] = None


class TraceabilityResponse(BaseModel):
    """Traceability response for a project."""
    project_id: str
    project: dict
    traceability: List[TraceabilityItem]


class NoteRequest(BaseModel):
    """Request for saving/updating a note."""
    req_id: str
    content: str


class NoteResponse(BaseModel):
    """Response for note operations."""
    success: bool
    note_id: Optional[str] = None
    content: Optional[str] = None
    updated_at: Optional[str] = None


def _determine_validation_status(requirement_id: str, defects: List[Defect]) -> str:
    """Determine validation status based on associated defects."""
    if not defects:
        return "passed"
    
    has_high_severity = any(defect.severity.lower() == "high" for defect in defects)
    has_medium_or_low = any(defect.severity.lower() in ["medium", "low"] for defect in defects)
    
    if has_high_severity:
        return "failed"
    elif has_medium_or_low:
        return "warning"
    else:
        return "passed"


def _extract_visual_elements(requirement_text: str) -> List[str]:
    """Extract visual elements from requirement text or use existing mappings."""
    # This is a simplified implementation
    # In a real system, this would query diagrams or use NLP to extract actors/use cases
    visual_elements = []
    
    # Simple keyword matching for actors
    actors = ["user", "admin", "manager", "system", "customer", "guest"]
    for actor in actors:
        if actor.lower() in requirement_text.lower():
            visual_elements.append(f"Actor: {actor.title()}")
    
    # Simple keyword matching for use cases
    use_cases = ["register", "login", "logout", "create", "update", "delete", "view", "search"]
    for use_case in use_cases:
        if use_case.lower() in requirement_text.lower():
            visual_elements.append(f"Use Case: {use_case.title()}")
    
    return visual_elements[:5]  # Limit to 5 elements


@router.get("/{project_id}", response_model=TraceabilityResponse)
async def get_traceability(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):

    """


    Get traceability data for all requirements in a project.
    Implements REQ_18: Requirements Traceability Matrix.
    """
    try:
        # Log authentication info for debugging
        logger.info(f"User {current_user.user_id} requesting traceability for project {project_id}")
        
        # Verify project exists first
        stmt = select(Project).where(Project.project_id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            logger.warning(f"Project {project_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Check if user has access (owner or shared access)
        if project.owner_id != current_user.user_id:
            logger.warning(f"User {current_user.user_id} does not have access to project {project_id} (owned by {project.owner_id})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't have permission to access this project"
            )
        
        logger.info(f"Access granted: User {current_user.user_id} accessing project {project.name}")
        
        # Get all requirements for the project
        stmt = select(Requirement).where(Requirement.project_id == project_id)
        result = await db.execute(stmt)
        requirements = result.scalars().all()
        
        logger.info(f"Found {len(requirements)} requirements for project {project_id}")
        
        traceability_items = []
        
        for req in requirements:
            # Get defects for this requirement
            stmt_defects = select(Defect).where(Defect.req_id == req.req_id)
            defects_result = await db.execute(stmt_defects)
            defects = defects_result.scalars().all()
            
            # Determine validation status
            validation_status = _determine_validation_status(req.req_id, defects)
            
            # Extract visual elements
            visual_elements = _extract_visual_elements(req.current_text or req.original_text)
            
            # Determine complexity
            complexity = determine_requirement_complexity(req.current_text or req.original_text)
            
            # Get note for this requirement
            stmt_note = (
                select(TraceabilityNote)
                .where(TraceabilityNote.req_id == req.req_id)
                .order_by(TraceabilityNote.created_at.desc())
                .limit(1)
            )
            note_result = await db.execute(stmt_note)
            note = note_result.scalars().first()
            
            note_data = None
            if note:
                note_data = {
                    "id": note.note_id,
                    "content": note.content,
                    "updated_at": note.created_at
                }
            
            # Create traceability item
            trace_item = TraceabilityItem(
                req_id=req.req_id,
                doc_id=req.doc_id,
                identifier=req.req_identifier or f"REQ-{req.sequence_order + 1:03d}",
                semantic_id=req.semantic_id,
                text=req.current_text or req.original_text,
                validation_status=validation_status,
                visual_elements=visual_elements,
                complexity=complexity,
                note=note_data
            )
            
            traceability_items.append(trace_item)
        
        return TraceabilityResponse(
            project_id=project_id,
            project={
                "id": project.project_id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at
            },
            traceability=traceability_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting traceability data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve traceability data"
        )


@router.get("/document/{doc_id}", response_model=TraceabilityResponse)
async def get_document_traceability(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get traceability data for a specific document.
    Allows document-level access from dashboard.
    """
    try:
        # Log authentication info for debugging
        logger.info(f"User {current_user.user_id} requesting traceability for document {doc_id}")
        
        # Verify document exists and user has access
        stmt = select(RequirementDocument).where(RequirementDocument.doc_id == doc_id)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            logger.warning(f"Document {doc_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        
        # Check if user has access (through project ownership)
        stmt_project = select(Project).where(Project.project_id == document.project_id)
        project_result = await db.execute(stmt_project)
        project = project_result.scalar_one_or_none()
        
        if not project or project.owner_id != current_user.user_id:
            logger.warning(f"User {current_user.user_id} does not have access to document {doc_id} (project {document.project_id})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't have permission to access this document"
            )
        
        logger.info(f"Access granted: User {current_user.user_id} accessing document {doc_id}")
        
        # Get requirements for this document only
        stmt_reqs = select(Requirement).where(Requirement.doc_id == doc_id)
        reqs_result = await db.execute(stmt_reqs)
        requirements = reqs_result.scalars().all()
        
        logger.info(f"Found {len(requirements)} requirements for document {doc_id}")
        
        traceability_items = []
        
        for req in requirements:
            # Get defects for this requirement
            stmt_defects = select(Defect).where(Defect.req_id == req.req_id)
            defects_result = await db.execute(stmt_defects)
            defects = defects_result.scalars().all()
            
            # Determine validation status
            validation_status = _determine_validation_status(req.req_id, defects)
            
            # Extract visual elements
            visual_elements = _extract_visual_elements(req.current_text or req.original_text)
            
            # Determine complexity
            complexity = determine_requirement_complexity(req.current_text or req.original_text)
            
            # Get note for this requirement
            stmt_note = (
                select(TraceabilityNote)
                .where(TraceabilityNote.req_id == req.req_id)
                .order_by(TraceabilityNote.created_at.desc())
                .limit(1)
            )
            note_result = await db.execute(stmt_note)
            note = note_result.scalars().first()
            
            note_data = None
            if note:
                note_data = {
                    "id": note.note_id,
                    "content": note.content,
                    "updated_at": note.created_at
                }
            
            # Create traceability item
            trace_item = TraceabilityItem(
                req_id=req.req_id,
                doc_id=req.doc_id,
                identifier=req.req_identifier or f"REQ-{req.sequence_order + 1:03d}",
                semantic_id=req.semantic_id,
                text=req.current_text or req.original_text,
                validation_status=validation_status,
                visual_elements=visual_elements,
                complexity=complexity,
                note=note_data
            )
            
            traceability_items.append(trace_item)
        
        return TraceabilityResponse(
            project_id=document.project_id,
            project={
                "id": project.project_id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at
            },
            traceability=traceability_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document traceability data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve traceability data"
        )


@router.post("/note", response_model=NoteResponse)
async def save_traceability_note(
    note_data: NoteRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Save or update a note for a requirement.
    Implements BR-16: User notes field with timestamp.
    """
    requirement = None
    try:
        # Verify requirement exists
        logger.info(f"Looking for requirement with req_id: {note_data.req_id}")
        stmt = select(Requirement).where(Requirement.req_id == note_data.req_id)
        result = await db.execute(stmt)
        requirement = result.scalar_one_or_none()
        
        logger.info(f"Found requirement: {requirement is not None}")
        if requirement:
            logger.info(f"Requirement details: req_id={requirement.req_id}, project_id={requirement.project_id}")
        
        if not requirement:
            logger.error(f"Requirement not found with req_id: {note_data.req_id}")
            # List all available requirements for debugging
            all_reqs_stmt = select(Requirement)
            all_reqs_result = await db.execute(all_reqs_stmt)
            all_reqs = all_reqs_result.scalars().all()
            logger.info(f"Available requirements in database: {[r.req_id for r in all_reqs[:10]]}")  # First 10
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requirement not found: {note_data.req_id}"
            )
        
        # Check if note already exists for this requirement
        stmt_note = (
            select(TraceabilityNote)
            .where(TraceabilityNote.req_id == note_data.req_id)
            .order_by(TraceabilityNote.created_at.desc())
            .limit(1)
        )
        note_result = await db.execute(stmt_note)
        existing_note = note_result.scalars().first()

        if existing_note:
            # Update existing note
            existing_note.content = note_data.content
            # NOTE: TraceabilityNote model only has created_at.
            # Treat it as the last-updated timestamp for backward compatibility.
            existing_note.created_at = datetime.now(timezone.utc).isoformat()
            await db.commit()
            await db.refresh(existing_note)

            return NoteResponse(
                success=True,
                note_id=existing_note.note_id,
                content=existing_note.content,
                updated_at=existing_note.created_at if isinstance(existing_note.created_at, str) else existing_note.created_at.isoformat()
            )
        else:
            # Create new note
            note = TraceabilityNote(
                req_id=note_data.req_id,
                created_by=current_user.user_id,
                project_id=requirement.project_id,
                content=note_data.content,
                note_type="traceability_annotation",
                created_at=datetime.now(timezone.utc).isoformat()
            )
            
            db.add(note)
            await db.commit()
            await db.refresh(note)
            
            return NoteResponse(
                success=True,
                note_id=note.note_id,
                content=note.content,
                updated_at=note.created_at if isinstance(note.created_at, str) else note.created_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving traceability note: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Note data: req_id={note_data.req_id}, content={note_data.content}")
        logger.error(f"User ID: {current_user.user_id}")
        logger.error(f"Requirement project_id: {requirement.project_id if requirement else 'None'}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save note: {str(e)}"
        )


@router.delete("/note/{note_id}", response_model=NoteResponse)
async def delete_traceability_note(
    note_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a traceability note.
    """
    try:
        # Get note and verify ownership
        stmt = select(TraceabilityNote).where(
            TraceabilityNote.note_id == note_id,
            TraceabilityNote.created_by == current_user.user_id
        )
        result = await db.execute(stmt)
        note = result.scalar_one_or_none()
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        # Delete note
        await db.delete(note)
        await db.commit()
        
        return NoteResponse(
            success=True,
            note_id=note_id,
            content="",
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting traceability note: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete note"
        )