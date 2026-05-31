"""Supervisor APIs for Module 6 (REQ_19 BR-18 BR-19).

Provides:
- Supervisor dashboard listing across all projects
- Supervisor read-only review view
- Supervisor review submission (approve / request changes)
- Creates notification rows for BR-19
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, asc, case, select



from models.user import User, UserRole
from models.project import Project
from models.document import RequirementDocument
from models.requirement import Requirement
from models.validation import ValidationSession, Defect
from models.traceability import TraceabilityMatrix, TraceabilityNote
from models.metrics import ProjectMetrics
from models.review import ReviewAudit
from models.notification import Notification
from utils.security import get_current_active_user, require_role
from config.database import get_db

router = APIRouter(tags=["supervisor"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SupervisorReviewDecision(BaseModel):
    decision: str  # "approved" | "changes_requested"
    comments: Optional[str] = None


async def _latest_validation_for_project(db: AsyncSession, project_id: str) -> Optional[ValidationSession]:
    stmt = (
        select(ValidationSession)
        .join(RequirementDocument, ValidationSession.doc_id == RequirementDocument.doc_id)
        .where(RequirementDocument.project_id == project_id)
        .order_by(ValidationSession.validation_date.desc())
        .limit(1)
    )
    res = await db.execute(stmt)
    return res.scalars().first()



@router.get("/dashboard")
async def supervisor_dashboard(
    current_user: User = Depends(require_role(UserRole.SUPERVISOR)),
    db: AsyncSession = Depends(get_db),
):

    """List all projects across all students for supervisor review."""
    result = await db.execute(select(Project).filter(Project.is_deleted == 0))
    projects = result.scalars().all()


    result: List[Dict[str, Any]] = []
    for p in projects:
        owner_result = await db.execute(select(User).where(User.user_id == p.owner_id))
        owner = owner_result.scalars().first()
        latest_val = await _latest_validation_for_project(db, p.project_id)

        quality_score = None
        defect_count = 0
        if latest_val:
            # overall_score stored in range 0..100 (see validation API)
            quality_score = latest_val.overall_score
            defect_count = latest_val.defect_count

        result.append(
            {
                "project_id": p.project_id,
                "name": p.name,
                "owner": owner.username if owner else p.owner_id,
                "quality_score": quality_score,
                "defect_count": defect_count,
                "status": p.status,
                "review_status": p.review_status,
            }
        )

    return result


@router.get("/review/{project_id}")
async def supervisor_review_view(

    project_id: str,
    current_user: User = Depends(require_role(UserRole.SUPERVISOR)),
    db: AsyncSession = Depends(get_db),
):
    """Read-only traceability / analysis data for supervisor."""
    project_result = await db.execute(
        select(Project).filter(Project.project_id == project_id, Project.is_deleted == 0).limit(1)
    )
    project = project_result.scalars().first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Collect requirements + defects + traceability notes for this project
    req_stmt = select(Requirement).where(Requirement.project_id == project_id)
    req_result = await db.execute(req_stmt)
    requirements = req_result.scalars().all()

    # Get document information for source document names
    doc_stmt = select(RequirementDocument)
    doc_result = await db.execute(doc_stmt)
    documents = {doc.doc_id: doc for doc in doc_result.scalars().all()}

    defects_by_req: Dict[str, List[Defect]] = {}
    defect_stmt = (
        select(Defect)
        .join(Requirement, Defect.req_id == Requirement.req_id)
        .where(Requirement.project_id == project_id)
    )
    defect_result = await db.execute(defect_stmt)
    defect_rows = defect_result.scalars().all()
    for d in defect_rows:
        defects_by_req.setdefault(d.req_id, []).append(d)

    notes_by_req: Dict[str, TraceabilityNote] = {}
    note_stmt = (
        select(TraceabilityNote)
        .where(TraceabilityNote.project_id == project_id)
        .order_by(TraceabilityNote.created_at.desc())
    )
    note_result = await db.execute(note_stmt)
    note_rows = note_result.scalars().all()
    # Keep latest note per req
    for n in note_rows:
        if n.req_id not in notes_by_req:
            notes_by_req[n.req_id] = n

    latest_val = await _latest_validation_for_project(db, project_id)
    metrics = None
    if latest_val:
        metrics_stmt = select(ProjectMetrics).where(
            ProjectMetrics.validation_id == latest_val.validation_id
        )
        metrics_result = await db.execute(metrics_stmt)
        metrics = metrics_result.scalars().first()


    traceability = []
    for req in requirements:
        req_defects = defects_by_req.get(req.req_id, [])
        validation_status = "passed"
        if req_defects:
            severities = {d.severity.lower() for d in req_defects}
            if "high" in severities:
                validation_status = "failed"
            elif "medium" in severities or "low" in severities:
                validation_status = "warning"

        latest_note = notes_by_req.get(req.req_id)
        # Get source document information
        source_document = documents.get(req.doc_id)
        source_document_name = source_document.filename if source_document else f"Document_{req.doc_id[:8]}"
        
        traceability.append(
            {
                "req_id": req.req_id,
                "identifier": req.req_identifier or f"REQ-{req.sequence_order + 1:03d}",
                "semantic_id": req.semantic_id,
                "text": req.current_text or req.original_text,
                "validation_status": validation_status,
                "defect_count": len(req_defects),
                "source_document": source_document_name,
                "doc_id": req.doc_id,
                "module_name": req.module_name,
                "section_header": req.section_header,
                "category": req.category,
                "category_confidence": req.category_confidence,
                "actors_json": req.actors_json,
                "modal_verbs_json": req.modal_verbs_json,
                "vague_terms_json": req.vague_terms_json,
                "word_count": req.word_count,
                "sequence_order": req.sequence_order,
                "visual_elements": req.visual_elements if hasattr(req, 'visual_elements') else None,
                "complexity": req.complexity if hasattr(req, 'complexity') else 'low',
                "defects": [
                    {
                        "defect_id": d.defect_id,
                        "type": d.defect_type,
                        "severity": d.severity,
                        "confidence": d.confidence_score,
                        "description": d.description,
                        "suggestion": d.ai_suggestion,
                        "req_id": d.req_id,
                    }
                    for d in req_defects
                ],
                "note": (
                    {
                        "note_id": latest_note.note_id,
                        "content": latest_note.content,
                        "created_at": latest_note.created_at,
                    }
                    if latest_note
                    else None
                ),
            }
        )

    return {
        "project": {
            "project_id": project.project_id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "review_status": project.review_status,
        },
        "metrics": (metrics.__dict__ if metrics else None),
        "traceability": traceability,
        "latest_validation": (
            {
                "validation_id": latest_val.validation_id,
                "overall_score": latest_val.overall_score,
                "defect_count": latest_val.defect_count,
                "status": latest_val.status,
                "validation_date": latest_val.validation_date,
            }
            if latest_val
            else None
        ),
    }


@router.post("/review/{project_id}")
def submit_supervisor_review(
    project_id: str,
    body: SupervisorReviewDecision,
    current_user: User = Depends(require_role(UserRole.SUPERVISOR)),
    db: Session = Depends(get_db),
):
    """Submit review decision and create review_audit + notification row (BR-19)."""
    decision = (body.decision or "").strip()
    comments = body.comments

    if decision not in ("approved", "changes_requested"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid decision")

    project = db.query(Project).filter(Project.project_id == project_id, Project.is_deleted == 0).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Get latest validation for audit metrics
    latest_val = _latest_validation_for_project(db, project.project_id)
    quality_score = latest_val.overall_score if latest_val else None
    defect_count = latest_val.defect_count if latest_val else 0

    # Create ReviewAudit record
    audit = ReviewAudit(
        review_id=str(uuid.uuid4()),
        project_id=project.project_id,
        supervisor_id=current_user.user_id,
        validation_id=latest_val.validation_id if latest_val else None,
        decision=decision,
        comments=comments,
        quality_score_at_review=quality_score,
        defect_count_at_review=defect_count,
        review_started_at=_now_iso(),
        review_completed_at=_now_iso(),
        created_at=_now_iso(),
    )
    db.add(audit)

    # Update project review_status
    project.review_status = decision

    # Update project timestamp
    project.updated_at = _now_iso()



    # Create notification for the project owner (student)
    notif_type = "review_approved" if decision == "approved" else "review_changes_requested"
    content = comments.strip() if comments else "No comments provided."

    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=project.owner_id,
        project_id=project.project_id,
        type=notif_type,
        content=content,
        is_read=False,
        created_at=_now_iso(),
    )
    db.add(notification)

    db.commit()
    db.refresh(notification)

    return {
        "success": True,
        "project_id": project.project_id,
        "review_status": project.review_status,
        "notification_id": notification.id,
        "review_audit_id": audit.review_id,
        "quality_score_at_review": quality_score,
        "defect_count_at_review": defect_count,
    }


@router.get("/review-queue")
def supervisor_review_queue(
    current_user: User = Depends(require_role(UserRole.SUPERVISOR)),
    db: Session = Depends(get_db),
):
    """Get projects pending review (not_reviewed or changes_requested)."""
    projects = (
        db.query(Project)
        .filter(
            Project.is_deleted == 0,
            Project.review_status.in_(["not_reviewed", "changes_requested"])
        )
        .order_by(Project.updated_at.desc())
        .all()
    )

    result: List[Dict[str, Any]] = []
    for p in projects:
        owner = db.query(User).filter(User.user_id == p.owner_id).first()
        latest_val = _latest_validation_for_project(db, p.project_id)

        quality_score = None
        defect_count = 0
        if latest_val:
            quality_score = latest_val.overall_score
            defect_count = latest_val.defect_count

        result.append(
            {
                "project_id": p.project_id,
                "name": p.name,
                "owner": owner.username if owner else p.owner_id,
                "owner_email": owner.email if owner else None,
                "quality_score": quality_score,
                "defect_count": defect_count,
                "status": p.status,
                "review_status": p.review_status,
                "last_updated": p.updated_at,
                "priority": "high" if (quality_score and quality_score < 50) else "medium" if (quality_score and quality_score < 70) else "low",
            }
        )

    return result


@router.get("/audit-history/{project_id}")
def supervisor_audit_history(
    project_id: str,
    current_user: User = Depends(require_role(UserRole.SUPERVISOR)),
    db: Session = Depends(get_db),
):
    """Get review audit history for a project."""
    project = db.query(Project).filter(Project.project_id == project_id, Project.is_deleted == 0).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    audits = (
        db.query(ReviewAudit)
        .filter(ReviewAudit.project_id == project_id)
        .order_by(ReviewAudit.created_at.desc())
        .all()
    )

    result = []
    for audit in audits:
        supervisor = db.query(User).filter(User.user_id == audit.supervisor_id).first()
        result.append(
            {
                "review_id": audit.review_id,
                "supervisor": supervisor.username if supervisor else "Unknown",
                "supervisor_email": supervisor.email if supervisor else None,
                "decision": audit.decision,
                "comments": audit.comments,
                "quality_score_at_review": audit.quality_score_at_review,
                "defect_count_at_review": audit.defect_count_at_review,
                "review_started_at": audit.review_started_at,
                "review_completed_at": audit.review_completed_at,
                "created_at": audit.created_at,
            }
        )

    return {
        "project_id": project_id,
        "project_name": project.name,
        "audit_history": result,
    }


@router.get("/metrics")
async def supervisor_metrics(
    current_user: User = Depends(require_role(UserRole.SUPERVISOR)),
    db: AsyncSession = Depends(get_db),
):
    """Get overall supervisor dashboard metrics."""

    total_projects = (await db.execute(
        select(func.count()).select_from(Project).where(Project.is_deleted == 0)
    )).scalar_one()

    # Count by review status
    async def _count_by_status(status_value: str) -> int:
        return (await db.execute(
            select(func.count()).select_from(Project).where(
                Project.is_deleted == 0,
                Project.review_status == status_value,
            )
        )).scalar_one()

    not_reviewed = await _count_by_status("not_reviewed")

    approved = await _count_by_status("approved")
    changes_requested = await _count_by_status("changes_requested")

    # Quality score distribution
    projects_with_scores: List[float] = []
    projects = (await db.execute(
        select(Project).where(Project.is_deleted == 0)
    )).scalars().all()

    for p in projects:
        latest_val = await _latest_validation_for_project(db, p.project_id)
        if latest_val and latest_val.overall_score is not None:
            projects_with_scores.append(latest_val.overall_score)

    avg_quality_score = sum(projects_with_scores) / len(projects_with_scores) if projects_with_scores else 0

    # Recent reviews
    recent_reviews = (
        await db.execute(
            select(ReviewAudit)
            .order_by(ReviewAudit.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    recent_reviews_data: List[Dict[str, Any]] = []
    for review in recent_reviews:
        project = (await db.execute(
            select(Project).where(Project.project_id == review.project_id)
        )).scalars().first()

        supervisor = (await db.execute(
            select(User).where(User.user_id == review.supervisor_id)
        )).scalars().first()

        recent_reviews_data.append(
            {
                "project_name": project.name if project else "Unknown",
                "supervisor": supervisor.username if supervisor else "Unknown",
                "decision": review.decision,
                "created_at": review.created_at,
            }
        )

    return {
        "total_projects": total_projects,
        "review_status_counts": {
            "not_reviewed": not_reviewed,
            "approved": approved,
            "changes_requested": changes_requested,
        },
        "average_quality_score": round(avg_quality_score, 2),
        "recent_reviews": recent_reviews_data,
        "review_completion_rate": round(
            ((approved + changes_requested) / total_projects * 100) if total_projects > 0 else 0,
            2,
        ),
    }



@router.get("/review-audits/{project_id}", response_model=List[dict])
def get_review_audits(
    project_id: str,
    current_user: User = Depends(require_role("supervisor")),
    db: Session = Depends(get_db),
):
    """Get the complete audit trail for a project's reviews."""
    audits = db.query(ReviewAudit).filter(ReviewAudit.project_id == project_id).order_by(ReviewAudit.created_at.desc()).all()
    
    return [
        {
            "id": audit.review_id,
            "project_id": audit.project_id,
            "reviewer_email": audit.supervisor_id,  # Use supervisor_id instead of reviewer_email
            "decision": audit.decision,
            "comments": audit.comments,
            "quality_score": audit.quality_score_at_review,
            "defect_count": audit.defect_count_at_review,
            "created_at": audit.created_at,
        }
        for audit in audits
    ]


@router.get("/reports", response_model=Dict[str, Any])
def get_supervisor_reports(
    current_user: User = Depends(require_role(UserRole.SUPERVISOR)),
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by project name or owner email"),
    review_status: Optional[str] = Query(None, description="Filter by review status"),
    min_quality: Optional[int] = Query(None, description="Minimum quality score"),
    max_quality: Optional[int] = Query(None, description="Maximum quality score"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get aggregated supervisor reports with filtering and pagination."""
    
    # Base query for projects with owner information
    projects_query = (
        db.query(Project, User)
        .join(User, Project.owner_id == User.user_id)
        .filter(Project.is_deleted == 0)
    )
    
    # Apply search filter
    if search:
        search_term = f"%{search}%"
        projects_query = projects_query.filter(
            (Project.name.ilike(search_term)) |
            (User.email.ilike(search_term))
        )
    
    # Apply review status filter
    if review_status and review_status != "all":
        projects_query = projects_query.filter(Project.review_status == review_status)
    
    # Get total count for pagination
    total_count = projects_query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    projects = projects_query.offset(offset).limit(page_size).all()
    
    # Get detailed information for each project
    project_reports = []
    quality_scores = []
    defect_counts = []
    review_status_counts = {"not_reviewed": 0, "approved": 0, "changes_requested": 0}
    
    for project, owner in projects:
        # Get latest validation session
        latest_validation = (
            db.query(ValidationSession)
            .filter(ValidationSession.project_id == project.project_id)
            .order_by(ValidationSession.validation_date.desc())
            .first()
        )
        
        # Get project metrics
        metrics = (
            db.query(ProjectMetrics)
            .join(ValidationSession, ProjectMetrics.validation_id == ValidationSession.validation_id)
            .filter(ValidationSession.project_id == project.project_id)
            .order_by(ValidationSession.validation_date.desc())
            .first()
        )
        
        # Get requirement counts
        req_stats = (
            db.query(
                func.count(Requirement.req_id).label('total_requirements'),
                func.sum(case((Requirement.validation_status == 'failed', 1), else_=0)).label('failed_count')
            )
            .filter(Requirement.project_id == project.project_id)
            .first()
        )
        
        # Get defect count
        defect_count = 0
        if latest_validation:
            defect_count = latest_validation.defect_count
        
        # Get quality score
        quality_score = 0
        if latest_validation:
            quality_score = latest_validation.overall_score
        
        # Apply quality score filters
        if min_quality is not None and quality_score < min_quality:
            continue
        if max_quality is not None and quality_score > max_quality:
            continue
        
        # Collect data for summary
        quality_scores.append(quality_score)
        defect_counts.append(defect_count)
        if project.review_status:
            review_status_counts[project.review_status] = review_status_counts.get(project.review_status, 0) + 1
        
        # Determine complexity level
        complexity_level = "Low"
        if metrics:
            if metrics.complexity_score >= 70:
                complexity_level = "High"
            elif metrics.complexity_score >= 40:
                complexity_level = "Medium"
        
        # Determine cost index
        cost_index = "Low"
        if metrics:
            if metrics.relative_cost_index >= 70:
                cost_index = "High"
            elif metrics.relative_cost_index >= 40:
                cost_index = "Medium"
        
        project_report = {
            "project_id": project.project_id,
            "name": project.name,
            "owner_email": owner.email,
            "created_at": project.created_at,
            "review_status": project.review_status or "not_reviewed",
            "quality_score": quality_score,
            "defect_count": defect_count,
            "total_requirements": req_stats.total_requirements if req_stats else 0,
            "failed_requirements": req_stats.failed_count if req_stats else 0,
            "complexity_score": metrics.complexity_score if metrics else 0,
            "complexity_level": complexity_level,
            "estimated_weeks": metrics.estimated_weeks if metrics else "Unknown",
            "cost_index": cost_index,
            "latest_validation_date": latest_validation.validation_date if latest_validation else None
        }
        
        project_reports.append(project_report)
    
    # Calculate summary statistics
    total_projects = len(project_reports)
    avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    total_defects = sum(defect_counts)
    
    summary = {
        "total_projects": total_projects,
        "average_quality_score": round(avg_quality_score, 1),
        "total_defects": total_defects,
        "approved_projects": review_status_counts.get("approved", 0),
        "pending_review": review_status_counts.get("not_reviewed", 0),
        "changes_requested": review_status_counts.get("changes_requested", 0)
    }
    
    return {
        "projects": project_reports,
        "summary": summary,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }

