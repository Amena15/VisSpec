"""Project management API routes."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.models.user import User
from backend.models.project import Project
from backend.models.document import RequirementDocument
from backend.models.requirement import Requirement
from backend.models.validation import ValidationSession
from backend.utils.security import get_current_active_user
from backend.config.database import get_db
from backend.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(
    name: str,
    description: str = "",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project for the authenticated user."""
    try:
        project = Project(
            project_id=str(uuid.uuid4()),
            owner_id=current_user.user_id,
            name=name,
            description=description,
            status="pending",
            created_at=_now_iso(),
            updated_at=_now_iso(),
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return {
            "project_id": project.project_id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at,
        }
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.get("/")
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects owned by authenticated user."""
    try:
        stmt = (
            select(Project)
            .where(
                Project.owner_id == current_user.user_id,
                Project.is_deleted == 0,
            )
            .order_by(Project.created_at.desc())
        )
        result = await db.execute(stmt)
        projects = result.scalars().all()

        project_ids = [project.project_id for project in projects]

        document_count_map = {}
        requirement_count_map = {}

        if project_ids:
            document_counts_result = await db.execute(
                select(
                    RequirementDocument.project_id,
                    func.count(RequirementDocument.doc_id).label("document_count"),
                )
                .where(
                    RequirementDocument.project_id.in_(project_ids),
                )
                .group_by(RequirementDocument.project_id)
            )
            document_count_map = {row.project_id: int(row.document_count or 0) for row in document_counts_result.all()}

            requirement_counts_result = await db.execute(
                select(
                    RequirementDocument.project_id,
                    func.count().label("requirements_count"),
                )
                .join(Requirement, Requirement.doc_id == RequirementDocument.doc_id)
                .where(
                    RequirementDocument.project_id.in_(project_ids),
                )
                .group_by(RequirementDocument.project_id)
            )
            requirement_count_map = {row.project_id: int(row.requirements_count or 0) for row in requirement_counts_result.all()}

        return [
            {
                "project_id": project.project_id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "review_status": project.review_status,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                "document_count": document_count_map.get(project.project_id, 0),
                "requirements_count": requirement_count_map.get(project.project_id, 0),
                "quality_score": None,
            }
            for project in projects
        ]
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single project by ID with its documents."""
    try:
        stmt = (
            select(Project)
            .where(
                Project.project_id == project_id,
                Project.owner_id == current_user.user_id,
                Project.is_deleted == 0,
            )
            .options(selectinload(Project.documents))
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        return {
            "project_id": project.project_id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "review_status": project.review_status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "documents": [
                {
                    "doc_id": d.doc_id,
                    "filename": d.filename,
                    "file_extension": d.file_extension,
                    "status": d.status,
                    "word_count": d.word_count,
                    "upload_date": d.upload_date,
                }
                for d in project.documents
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete a project and all associated data.
    Implements REQ_07: Project Data Management with cascade delete.
    """
    try:
        # Load project with its documents and their requirements using selectinload
        stmt = (
            select(Project)
            .where(
                Project.project_id == project_id,
                Project.owner_id == current_user.user_id,
            )
            .options(
                selectinload(Project.documents).selectinload(RequirementDocument.requirements)
            )
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Count associated records before deletion
        doc_count = len(project.documents)
        req_count = sum(len(doc.requirements) for doc in project.documents)
        val_count = sum(len(doc.validation_sessions) for doc in project.documents)

        await db.delete(project)
        await db.commit()

        return {
            "message": "Project and all associated data permanently deleted",
            "project_id": project_id,
            "deleted_documents": doc_count,
            "deleted_requirements": req_count,
            "deleted_validation_sessions": val_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )