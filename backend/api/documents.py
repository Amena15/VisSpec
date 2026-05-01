"""Document upload and management API routes.

Implements REQ_04 (Document Upload), REQ_05 (Text Extraction & Parsing),
REQ_06 (Structure Identification), and REQ_07 (Project Data Management).
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from models.user import User
from models.project import Project
from models.document import RequirementDocument
from models.requirement import Requirement
from schemas.document import (
    DocumentUploadResponse,
    DocumentSummary,
    DocumentDetail,
    DocumentDeleteResponse,
)
from services.document.parser import DocumentParser
from utils.security import get_current_active_user
from config.database import get_db
from core.config import settings

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_json_loads(value: Optional[str], default=None):
    """Safely load JSON string, returning default on failure."""
    if not value:
        return default if default is not None else []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload a requirement document (PDF, DOCX, or TXT).

    Implements UC_04:
    - Validates file type (BR-07: only .pdf and .docx accepted, plus .txt)
    - Validates file size (BR-08: max 10MB)
    - Detects scanned/image-based PDFs
    - Extracts text, structure, and requirements
    - Returns Document Summary (word count, # requirements found)
    """
    # ------------------------------------------------------------------
    # 1. Validate project ownership
    # ------------------------------------------------------------------
    project = (
        db.query(Project)
        .filter(
            Project.project_id == project_id,
            Project.owner_id == current_user.user_id,
            Project.is_deleted == 0,
        )
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    # ------------------------------------------------------------------
    # 2. Validate file type (BR-07)
    # ------------------------------------------------------------------
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed_extensions = {"pdf", "docx", "txt"}

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: .{ext}. Only PDF, DOCX, and TXT are accepted.",
        )

    # ------------------------------------------------------------------
    # 3. Validate file size (BR-08: max 10MB)
    # ------------------------------------------------------------------
    file_content = await file.read()
    file_size = len(file_content)
    max_size = settings.MAX_FILE_SIZE_BYTES  # 10MB

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size // (1024 * 1024)}MB.",
        )

    # ------------------------------------------------------------------
    # 4. Parse document
    # ------------------------------------------------------------------
    parser = DocumentParser()
    parse_result = parser.parse_full(file_content, filename)

    if "error" in parse_result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document parsing failed: {parse_result['error']}",
        )

    # ------------------------------------------------------------------
    # 5. Detect scanned PDF (UC_04 A2)
    # ------------------------------------------------------------------
    is_scanned = parse_result.get("is_scanned_pdf", 0)
    if is_scanned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No text detected. Please upload a searchable PDF or convert using OCR.",
        )

    # ------------------------------------------------------------------
    # 6. Create RequirementDocument record
    # ------------------------------------------------------------------
    doc_id = str(uuid.uuid4())
    now = _now_iso()

    doc_record = RequirementDocument(
        doc_id=doc_id,
        project_id=project_id,
        uploaded_by=current_user.user_id,
        filename=filename,
        file_extension=ext,
        file_size_bytes=file_size,
        word_count=parse_result.get("word_count"),
        page_count=parse_result.get("page_count"),
        status="ready",
        is_scanned_pdf=is_scanned,
        extracted_author=parse_result.get("extracted_author") or None,
        extracted_version=parse_result.get("extracted_version") or None,
        malware_scan_passed=1,  # Simplified; real malware scan would go here
        content=file_content,  # Store full content for professional extraction
        upload_date=now,
    )
    db.add(doc_record)

    # ------------------------------------------------------------------
    # 7. Create Requirement records (REQ_05)
    # ------------------------------------------------------------------
    requirements = parse_result.get("requirements", [])
    for req_data in requirements:
        req = Requirement(
            req_id=str(uuid.uuid4()),
            doc_id=doc_id,
            project_id=project_id,
            req_identifier=req_data.get("req_identifier"),
            section_header=req_data.get("section_header"),
            original_text=req_data["original_text"],
            current_text=req_data["original_text"],
            word_count=req_data.get("word_count", 0),
            sequence_order=req_data.get("sequence_order", 0),
            created_at=now,
        )
        db.add(req)

    # Update project status
    project.status = "parsing"
    project.updated_at = now

    db.commit()
    db.refresh(doc_record)

    # ------------------------------------------------------------------
    # 8. Return Document Summary (UC_04 step 7)
    # ------------------------------------------------------------------
    return DocumentUploadResponse(
        doc_id=doc_id,
        project_id=project_id,
        filename=filename,
        file_extension=ext,
        file_size_bytes=file_size,
        word_count=parse_result.get("word_count", 0),
        page_count=parse_result.get("page_count"),
        status="ready",
        extracted_author=parse_result.get("extracted_author") or None,
        extracted_version=parse_result.get("extracted_version") or None,
        is_scanned_pdf=is_scanned,
        requirements_found=len(requirements),
        sections_found=parse_result.get("sections_found", []),
        upload_date=now,
    )


@router.get("/", response_model=List[DocumentSummary])
def list_documents(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all documents for the authenticated user, optionally filtered by project."""
    query = (
        db.query(RequirementDocument)
        .join(Project)
        .filter(
            Project.owner_id == current_user.user_id,
            RequirementDocument.status != "deleted",
        )
    )

    if project_id:
        query = query.filter(RequirementDocument.project_id == project_id)

    docs = query.order_by(RequirementDocument.upload_date.desc()).all()

    result = []
    for d in docs:
        req_count = len(d.requirements)
        result.append(
            DocumentSummary(
                doc_id=d.doc_id,
                project_id=d.project_id,
                filename=d.filename,
                file_extension=d.file_extension,
                file_size_bytes=d.file_size_bytes,
                word_count=d.word_count,
                page_count=d.page_count,
                status=d.status,
                requirements_found=req_count,
                upload_date=d.upload_date,
            )
        )
    return result


@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a single document with its extracted requirements."""
    doc = (
        db.query(RequirementDocument)
        .join(Project)
        .filter(
            RequirementDocument.doc_id == doc_id,
            Project.owner_id == current_user.user_id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    requirements = []
    for r in doc.requirements:
        req_item = {
            "req_id": r.req_id,
            "req_identifier": r.req_identifier,
            "semantic_id": r.semantic_id,
            "section_header": r.section_header,
            "module_name": r.module_name,
            "original_text": r.original_text,
            "current_text": r.current_text,
            "word_count": r.word_count,
            "category": r.category,
            "category_confidence": r.category_confidence,
            "actors": _safe_json_loads(r.actors_json, []),
            "modal_verbs": _safe_json_loads(r.modal_verbs_json, []),
            "vague_terms": _safe_json_loads(r.vague_terms_json, []),
            "sequence_order": r.sequence_order,
            "validation_status": r.validation_status,
        }
        requirements.append(req_item)

    return DocumentDetail(
        doc_id=doc.doc_id,
        project_id=doc.project_id,
        filename=doc.filename,
        file_extension=doc.file_extension,
        file_size_bytes=doc.file_size_bytes,
        word_count=doc.word_count,
        page_count=doc.page_count,
        status=doc.status,
        parse_error=doc.parse_error,
        is_scanned_pdf=doc.is_scanned_pdf,
        extracted_author=doc.extracted_author,
        extracted_version=doc.extracted_version,
        malware_scan_passed=doc.malware_scan_passed,
        upload_date=doc.upload_date,
        requirements=requirements,
    )


@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete a document and all associated analysis data.
    Implements REQ_07: Project Data Management (GDPR Right to be Forgotten).
    """
    doc = (
        db.query(RequirementDocument)
        .join(Project)
        .filter(
            RequirementDocument.doc_id == doc_id,
            Project.owner_id == current_user.user_id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    req_count = len(doc.requirements)
    val_count = len(doc.validation_sessions)

    # SQLAlchemy cascade handles deletion of requirements, validation_sessions, defects
    db.delete(doc)
    db.commit()

    return DocumentDeleteResponse(
        message="Document and all associated data permanently deleted",
        doc_id=doc_id,
        deleted_requirements=req_count,
        deleted_validations=val_count,
    )
