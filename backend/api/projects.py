"""Project management API routes."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List

from models.user import User
from models.project import Project
from models.document import RequirementDocument
from models.validation import ValidationSession
from utils.security import get_current_active_user
from config.database import get_db

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_project(
    name: str,
    description: str = "",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new project for the authenticated user."""
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
    db.commit()
    db.refresh(project)
    return {
        "project_id": project.project_id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at,
    }


@router.get("/")
def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all projects owned by authenticated user."""
    try:
        projects = (
            db.query(Project)
            .filter(Project.owner_id == current_user.user_id, Project.is_deleted == 0)
            .all()
        )
        result = []
        for p in projects:
            # Count requirements across all documents in this project
            req_count = 0
            doc_count = 0
            if p.documents:
                doc_count = len(p.documents)
                print(f"DEBUG: Project {p.name} has {doc_count} documents")
                for doc in p.documents:
                    print(f"DEBUG: Document {doc.filename} has {len(doc.requirements) if doc.requirements else 0} requirements")
                    if doc.requirements:
                        req_count += len(doc.requirements)
            
            print(f"DEBUG: Project {p.name} total requirements: {req_count}")
            result.append({
                "project_id": p.project_id,
                "name": p.name,
                "description": p.description,
                "status": p.status,
                "review_status": p.review_status,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "document_count": doc_count,
                "requirements_count": req_count,
                "quality_score": "N/A"  # TODO: Compute from validation results
            })
        return result
    except Exception as e:
        print(f"Error in projects API: {e}")
        return []


@router.get("/{project_id}")
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a single project by ID with its documents."""
    project = (
        db.query(Project)
        .options(joinedload(Project.documents))
        .filter(
            Project.project_id == project_id,
            Project.owner_id == current_user.user_id,
            Project.is_deleted == 0,
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
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


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete a project and all associated data.
    Implements REQ_07: Project Data Management with cascade delete.
    """
    project = (
        db.query(Project)
        .filter(
            Project.project_id == project_id,
            Project.owner_id == current_user.user_id,
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Count associated records before deletion for the response
    doc_count = len(project.documents)
    req_count = sum(len(d.requirements) for d in project.documents)
    val_count = len(project.validation_sessions)

    # SQLAlchemy cascade="all, delete-orphan" handles the rest
    db.delete(project)
    db.commit()

    return {
        "message": "Project and all associated data permanently deleted",
        "project_id": project_id,
        "deleted_documents": doc_count,
        "deleted_requirements": req_count,
        "deleted_validation_sessions": val_count,
    }

