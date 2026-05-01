"""Validation API routes.

Implements UC_05: Validate Requirements.
"""
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from models.user import User
from models.project import Project
from models.document import RequirementDocument
from models.requirement import Requirement
from models.validation import ValidationSession, Defect
from utils.security import get_current_active_user
from config.database import get_db
from services.validation.validator import Validator
from core.config import settings
from core.logging import get_logger
from schemas.validation import (
    ValidationRequest,
    ValidationResponse,
    DefectResponse,
    DocumentValidationRequest,
    DocumentValidationResponse,
)

router = APIRouter(prefix="/api/validation", tags=["validation"])
logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@router.post("/validate", response_model=ValidationResponse)
def validate_requirements(
    request: ValidationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Run the full validation pipeline on raw requirements text.
    Detects ambiguities, inconsistencies, incompleteness, and unverifiable items.
    """
    try:
        validator = Validator(use_llm=True)
        result = validator.validate_text(request.text)

        return ValidationResponse(
            overall_score=result["overall_score"],
            total_defects=result["total_defects"],
            defects_by_type=result["defects_by_type"],
            defects_by_severity=result["defects_by_severity"],
            defects=[DefectResponse(**d) for d in result["defects"]],
            llm_used=result["llm_used"],
            processing_time_ms=result["processing_time_ms"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )


@router.post("/validate-document", response_model=DocumentValidationResponse)
def validate_document(
    request: DocumentValidationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Run validation on an uploaded document by doc_id.
    """
    now = _now_iso()
    validation_id = str(uuid.uuid4())

    # ------------------------------------------------------------------
    # 1. Verify document exists and user has access
    # ------------------------------------------------------------------
    doc = (
        db.query(RequirementDocument)
        .join(Project)
        .filter(
            RequirementDocument.doc_id == request.doc_id,
            Project.owner_id == current_user.user_id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Get requirements for the document
    requirements = doc.requirements
    if not requirements:
        return DocumentValidationResponse(
            validation_id=validation_id,
            doc_id=request.doc_id,
            project_id=doc.project_id,
            status="completed",
            overall_score=100.0,
            total_defects=0,
            total_requirements=0,
            defects_by_type={},
            defects_by_severity={},
            defects=[],
            llm_used=False,
            processing_time_ms=0,
            perfect_score=True,
        )

    # ------------------------------------------------------------------
    # 2. Create ValidationSession record (status: running)
    # ------------------------------------------------------------------
    val_session = ValidationSession(
        validation_id=validation_id,
        project_id=doc.project_id,
        doc_id=doc.doc_id,
        triggered_by=current_user.user_id,
        status="running",
        total_requirements=len(requirements),
        llm_model_used=settings.GROQ_MODEL,
        zero_retention_confirmed=1,
        validation_date=now,
    )
    db.add(val_session)
    db.commit()

    # ------------------------------------------------------------------
    # 3. Determine if requirements are enriched and run appropriate validator
    # ------------------------------------------------------------------
    is_enriched = any(r.category for r in requirements)

    try:
        validator = Validator(use_llm=True)
        if is_enriched:
            # Use context-aware validation with classification data
            req_contexts = []
            for r in requirements:
                req_contexts.append({
                    "req_id": r.req_id,
                    "original_text": r.original_text,
                    "category": r.category,
                    "vague_terms": _safe_json_loads(r.vague_terms_json, []),
                    "modal_verbs": _safe_json_loads(r.modal_verbs_json, []),
                })
            result = validator.validate_requirements_with_context(req_contexts)
        else:
            # Fallback: validate combined text
            combined_text = "\n\n".join(r.original_text for r in requirements)
            result = validator.validate_text(combined_text)

        llm_used = result.get("llm_used", False)
        processing_time_ms = result.get("processing_time_ms", 0)
    except Exception as e:
        logger.warning(f"Validation attempt 1 failed: {e}")
        # Automatic retry (max 1 retry as per UC_05 A1)
        try:
            val_session.api_retries = 1
            db.commit()
            validator = Validator(use_llm=True)
            if is_enriched:
                req_contexts = []
                for r in requirements:
                    req_contexts.append({
                        "req_id": r.req_id,
                        "original_text": r.original_text,
                        "category": r.category,
                        "vague_terms": _safe_json_loads(r.vague_terms_json, []),
                        "modal_verbs": _safe_json_loads(r.modal_verbs_json, []),
                    })
                result = validator.validate_requirements_with_context(req_contexts)
            else:
                combined_text = "\n\n".join(r.original_text for r in requirements)
                result = validator.validate_text(combined_text)
            llm_used = result.get("llm_used", False)
            processing_time_ms = result.get("processing_time_ms", 0)
        except Exception as e2:
            logger.error(f"Validation retry also failed: {e2}")
            val_session.status = "failed"
            val_session.error_message = "Analysis service is currently busy. Please try again in a few minutes."
            db.commit()
            return DocumentValidationResponse(
                validation_id=validation_id,
                doc_id=request.doc_id,
                project_id=doc.project_id,
                status="failed",
                error_message="Analysis service is currently busy. Please try again in a few minutes.",
                total_requirements=len(requirements),
            )

    # ------------------------------------------------------------------
    # 4. Filter defects by confidence threshold (BR-10: > 70%)
    # ------------------------------------------------------------------
    all_defects = result.get("defects", [])
    filtered_defects = [d for d in all_defects if d.get("confidence", 0) > settings.MIN_CONFIDENCE_THRESHOLD]

    # ------------------------------------------------------------------
    # 5. Save defects to database with proper req_id mapping
    # ------------------------------------------------------------------
    defect_count = 0
    ambiguity_count = 0
    incompleteness_count = 0
    inconsistency_count = 0
    unverifiable_count = 0

    # Track defects per requirement for validation_status update
    req_defect_counts = {}

    for d in filtered_defects:
        req_id = d.get("req_id")
        # Fallback: if no req_id mapped, use text similarity
        if not req_id and requirements:
            req_id = validator._find_best_match(d.get("text", ""), [
                {"req_id": r.req_id, "original_text": r.original_text} for r in requirements
            ])

        defect = Defect(
            defect_id=str(uuid.uuid4()),
            validation_id=validation_id,
            req_id=req_id,
            defect_type=d["type"],
            severity=d["severity"],
            confidence_score=d["confidence"],
            description=d["description"],
            ai_suggestion=d.get("suggestion"),
            detected_at=now,
        )
        db.add(defect)
        defect_count += 1

        # Track per-requirement defect counts
        if req_id:
            req_defect_counts[req_id] = req_defect_counts.get(req_id, 0) + 1

        if d["type"] == "ambiguity":
            ambiguity_count += 1
        elif d["type"] == "incompleteness":
            incompleteness_count += 1
        elif d["type"] == "inconsistency":
            inconsistency_count += 1
        elif d["type"] == "unverifiable":
            unverifiable_count += 1

    # ------------------------------------------------------------------
    # 6. Update per-requirement validation_status
    # ------------------------------------------------------------------
    for req in requirements:
        count = req_defect_counts.get(req.req_id, 0)
        if count == 0:
            req.validation_status = "passed"
        elif any(d.get("req_id") == req.req_id and d.get("severity") == "high" for d in filtered_defects):
            req.validation_status = "failed"
        else:
            req.validation_status = "warning"

    # ------------------------------------------------------------------
    # 7. Update ValidationSession
    # ------------------------------------------------------------------
    val_session.status = "completed"
    val_session.overall_score = result.get("overall_score", 0.0) * 100  # Scale to 0-100
    val_session.defect_count = defect_count
    val_session.ambiguity_count = ambiguity_count
    val_session.incompleteness_count = incompleteness_count
    val_session.inconsistency_count = inconsistency_count
    val_session.unverifiable_count = unverifiable_count
    val_session.processing_time_ms = processing_time_ms
    db.commit()

    # ------------------------------------------------------------------
    # 8. Build response
    # ------------------------------------------------------------------
    perfect_score = defect_count == 0

    return DocumentValidationResponse(
        validation_id=validation_id,
        doc_id=request.doc_id,
        project_id=doc.project_id,
        status="completed",
        overall_score=val_session.overall_score,
        total_defects=defect_count,
        total_requirements=len(requirements),
        defects_by_type=result.get("defects_by_type", {}),
        defects_by_severity=result.get("defects_by_severity", {}),
        defects=[DefectResponse(**d) for d in filtered_defects],
        llm_used=llm_used,
        processing_time_ms=processing_time_ms,
        perfect_score=perfect_score,
    )


@router.post("/validate-batch", response_model=Dict[str, Any])
def validate_batch_requirements(
    request: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Validate multiple requirements texts at once.
    """
    try:
        texts = request.get("texts", [])
        if not texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No requirement texts provided",
            )

        validator = Validator(use_llm=True)
        result = validator.validate_multiple(texts)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch validation failed: {str(e)}",
        )


@router.get("/validation-results/{doc_id}", response_model=DocumentValidationResponse)
def get_validation_results(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve validation results for a document, including defects with proper requirement linking.
    """
    # Verify document exists and user has access
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Get the latest validation session for this document
    val_session = (
        db.query(ValidationSession)
        .filter(ValidationSession.doc_id == doc_id)
        .order_by(ValidationSession.validation_date.desc())
        .first()
    )
    
    if not val_session:
        return DocumentValidationResponse(
            validation_id="",
            doc_id=doc_id,
            project_id=doc.project_id,
            status="pending",
            overall_score=None,
            total_defects=0,
            total_requirements=len(doc.requirements),
            defects_by_type={},
            defects_by_severity={},
            defects=[],
            llm_used=False,
            processing_time_ms=0,
            perfect_score=False,
        )

    # Get defects for this validation session with requirement details
    defects = (
        db.query(Defect, Requirement)
        .join(Requirement, Defect.req_id == Requirement.req_id, isouter=True)
        .filter(Defect.validation_id == val_session.validation_id)
        .all()
    )

    defect_responses = []
    defects_by_type = {}
    defects_by_severity = {}

    for defect, requirement in defects:
        defect_type = defect.defect_type
        severity = defect.severity
        
        # Update counts
        defects_by_type[defect_type] = defects_by_type.get(defect_type, 0) + 1
        defects_by_severity[severity] = defects_by_severity.get(severity, 0) + 1

        # Create defect response with proper requirement linking
        defect_response = DefectResponse(
            text=requirement.original_text if requirement else "Unknown requirement",
            type=defect_type,
            severity=severity,
            confidence=defect.confidence_score,
            description=defect.description,
            suggestion=defect.ai_suggestion,
            req_id=defect.req_id  # This will now always be included
        )
        defect_responses.append(defect_response)

    return DocumentValidationResponse(
        validation_id=val_session.validation_id,
        doc_id=doc_id,
        project_id=doc.project_id,
        status=val_session.status,
        overall_score=val_session.overall_score,
        total_defects=len(defect_responses),
        total_requirements=len(doc.requirements),
        defects_by_type=defects_by_type,
        defects_by_severity=defects_by_severity,
        defects=defect_responses,
        llm_used=val_session.llm_model_used is not None,
        processing_time_ms=val_session.processing_time_ms,
        perfect_score=len(defect_responses) == 0,
    )


def _safe_json_loads(value, default=None):
    """Safely load JSON string, returning default on failure."""
    if not value:
        return default if default is not None else []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []
