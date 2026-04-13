"""Validation API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from models.user import User
from utils.security import get_current_active_user
from config.database import get_db
from services.validation.validator import Validator
from schemas.validation import (
    ValidationRequest,
    ValidationResponse,
    DefectResponse,
)

router = APIRouter(prefix="/api/validation", tags=["validation"])


@router.post("/validate", response_model=ValidationResponse)
def validate_requirements(
    request: ValidationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Run the full validation pipeline on requirements text.
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
