"""
Fixed enrichment API with enhanced database handling and fallback
(Async version compatible with `AsyncSession`)
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Any, List, Optional
import json
import logging
import traceback
from datetime import datetime, timezone
from pydantic import BaseModel, validator

from backend.models.user import User
from backend.models.document import RequirementDocument
from backend.models.requirement import Requirement
from backend.models.project import Project
from backend.config.database import get_db
from backend.utils.security import get_current_active_user
from backend.services.ai.requirement_organizer import requirement_organizer
from backend.services.ai.text_cleaner import TextCleaner
from backend.core.logging import get_logger


# Pydantic models for request/response
class ApplySuggestionRequest(BaseModel):
    req_id: str
    new_text: str
    
    @validator('new_text')
    def validate_new_text(cls, v):
        if not v or not v.strip():
            raise ValueError('New text cannot be empty')
        if len(v) > 5000:
            raise ValueError('New text exceeds maximum length of 5000 characters')
        return v.strip()

class UndoSuggestionRequest(BaseModel):
    req_id: str
    
    @validator('req_id')
    def validate_req_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Requirement ID cannot be empty')
        return v.strip()

logger = get_logger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])

@router.post("/enrich/{doc_id}")
async def enrich_requirements(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    ENHANCED: Organize, classify, and enrich requirements for a document (Async).
    Enforces document access control (ownership validation).
    """
    try:
        logger.info(
            f"Starting enhanced enrichment for doc_id={doc_id}",
            extra={"user_id": current_user.user_id}
        )

        # 1. Retrieve document and verify ownership (SECURITY)
        doc_res = await db.execute(
            select(RequirementDocument).filter(RequirementDocument.doc_id == doc_id)
        )
        doc = doc_res.scalar_one_or_none()

        if not doc:
            logger.warning(
                "Document not found for enrichment",
                extra={"doc_id": doc_id, "user_id": current_user.user_id},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        
        # Verify document ownership
        if doc.uploaded_by != current_user.user_id:
            logger.warning(
                "Unauthorized access attempt to document enrichment",
                extra={"doc_id": doc_id, "user_id": current_user.user_id, "owner_id": doc.uploaded_by},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        
        # 2. Retrieve and requirements (async)
        logger.info(
            f"Retrieving requirements for doc_id={doc_id}",
            extra={"user_id": current_user.user_id}
        )

        req_res = await db.execute(
            select(Requirement)
            .filter(Requirement.doc_id == doc_id)
            .order_by(Requirement.sequence_order)
        )
        requirements = req_res.scalars().all()

        if not requirements:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No requirements found in this document.",
            )

        logger.info(f"Found {len(requirements)} requirements for processing")

        # 2. Build requirements list and apply text cleaning
        raw_reqs = []
        for r in requirements:
            raw_reqs.append({
                "req_id": r.req_id,
                "req_identifier": r.req_identifier,
                "section_header": r.section_header,
                "original_text": r.original_text,
                "current_text": r.current_text,
                "word_count": r.word_count,
                "sequence_order": r.sequence_order,
            })

        cleaned_reqs = TextCleaner.clean_requirements_batch(raw_reqs)

        cleaning_improvements = 0
        for i, cleaned in enumerate(cleaned_reqs):
            if cleaned["original_text"] != raw_reqs[i]["original_text"]:
                cleaning_improvements += 1

        logger.info(f"Text cleaning improved {cleaning_improvements} requirements")

        # 3. Run organization with fallback
        full_text = "\n\n".join(req["original_text"] for req in cleaned_reqs)

        try:
            enriched_reqs = requirement_organizer.organize_and_enrich(
                requirements=cleaned_reqs,
                full_text=full_text,
                use_llm=True,
            )
            if not enriched_reqs:
                raise Exception("LLM enrichment returned no requirements")
            logger.info(f"LLM organization successful: {len(enriched_reqs)} requirements")

        except Exception as org_error:
            logger.warning(f"LLM organization failed: {org_error}. Falling back to rule-based.")
            enriched_reqs = requirement_organizer.organize_and_enrich(
                requirements=cleaned_reqs,
                full_text=full_text,
                use_llm=False,
            )

        # Ensure DB update even if enrichment produced an empty list.
        if not enriched_reqs:
            logger.warning("Enrichment produced empty results; forcing deterministic DB update")
            enriched_reqs = []
            for req in cleaned_reqs:
                enriched_reqs.append({
                    **req,
                    "semantic_id": f"REQ-{req['sequence_order']:03d}",
                    "module_name": "General",
                    "category": "functional",
                    "category_confidence": 0.5,
                    "actors": [],
                    "modal_verbs": [],
                    "vague_terms": [],
                })
            logger.info(f"Deterministic fallback applied: {len(enriched_reqs)} requirements")

        # 4. Enhanced database update with multiple attempts
        updated_count = 0
        db_errors = []
        max_commit_attempts = 3
        commit_success = False

        for commit_attempt in range(max_commit_attempts):
            try:
                logger.info(f"Database commit attempt {commit_attempt + 1}/{max_commit_attempts}")
                updated_count = 0
                db_errors = []

                for enriched in enriched_reqs:
                    try:
                        req_id = enriched.get("req_id")
                        if not req_id:
                            logger.warning("Skipping enriched requirement with no req_id")
                            continue

                        req_res = await db.execute(
                            select(Requirement).filter(Requirement.req_id == req_id)
                        )
                        req = req_res.scalar_one_or_none()
                        if not req:
                            logger.warning(f"Requirement not found in DB: {req_id}")
                            continue

                        # Update fields with validation
                        req.semantic_id = enriched.get("semantic_id") or req.semantic_id
                        req.module_name = enriched.get("module_name") or req.module_name
                        req.category = enriched.get("category") or req.category
                        req.category_confidence = enriched.get("category_confidence", req.category_confidence or 0.5)

                        actors = enriched.get("actors", [])
                        modal_verbs = enriched.get("modal_verbs", [])
                        vague_terms = enriched.get("vague_terms", [])

                        req.actors_json = json.dumps(actors) if actors else req.actors_json
                        req.modal_verbs_json = json.dumps(modal_verbs) if modal_verbs else req.modal_verbs_json
                        req.vague_terms_json = json.dumps(vague_terms) if vague_terms else req.vague_terms_json

                        cleaned_text = enriched.get("original_text", req.current_text)
                        if cleaned_text and cleaned_text != req.original_text:
                            req.original_text = cleaned_text
                            req.current_text = cleaned_text
                            logger.info(f"Updated both original_text and current_text for {req_id}")

                        updated_count += 1

                    except Exception as req_error:
                        error_msg = f"Error updating {enriched.get('req_id', 'unknown')}: {req_error}"
                        db_errors.append(error_msg)
                        logger.error(error_msg)
                        continue

                # Flush and commit
                await db.flush()
                await db.commit()
                logger.info(f"✅ Database commit successful: {updated_count} requirement updates committed")
                commit_success = True
                break

            except Exception as commit_error:
                logger.error(f"❌ Database commit attempt {commit_attempt + 1} failed: {commit_error}")
                await db.rollback()
                if commit_attempt < max_commit_attempts - 1:
                    logger.info("Retrying commit in 2 seconds...")
                    import asyncio
                    await asyncio.sleep(2)
                else:
                    raise commit_error

        if not commit_success:
            logger.error("All commit attempts failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database update failed after multiple attempts"
            )

        # 5. Build enhanced response
        result_requirements = []
        for enriched in enriched_reqs:
            result_requirements.append({
                "req_id": enriched.get("req_id"),
                "req_identifier": enriched.get("req_identifier"),
                "semantic_id": enriched.get("semantic_id"),
                "section_header": enriched.get("section_header"),
                "module_name": enriched.get("module_name"),
                "category": enriched.get("category"),
                "category_confidence": enriched.get("category_confidence"),
                "original_text": enriched.get("original_text"),
                "actors": enriched.get("actors", []),
                "modal_verbs": enriched.get("modal_verbs", []),
                "vague_terms": enriched.get("vague_terms", []),
            })

        category_counts = {}
        module_counts = {}
        semantic_ids_generated = 0

        for req in result_requirements:
            category = req.get("category", "uncategorized")
            module = req.get("module_name", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
            module_counts[module] = module_counts.get(module, 0) + 1
            if req.get("semantic_id"):
                semantic_ids_generated += 1

        # Build response (sanitized - no sensitive error details)
        response = {
            "message": "Requirements organized and enriched successfully",
            "total_requirements": len(result_requirements),
            "updated_requirements": updated_count,
            "cleaning_improvements": cleaning_improvements,
            "semantic_ids_generated": semantic_ids_generated,
            "category_distribution": category_counts,
            "module_distribution": module_counts,
            "requirements": result_requirements,
            "doc_id": doc_id,
        }
        
        # Log database errors for debugging but don't expose to client
        if db_errors:
            logger.warning(
                f"Database errors during enrichment (count={len(db_errors)})",
                extra={"doc_id": doc_id, "error_count": len(db_errors), "sample_errors": db_errors[:3]}
            )
        
        logger.info(
            f"Enrichment completed successfully: {updated_count} requirements updated",
            extra={"doc_id": doc_id, "user_id": current_user.user_id, "count": updated_count}
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Enhanced enrichment failed for doc_id={doc_id}",
            extra={"doc_id": doc_id, "user_id": current_user.user_id, "error": str(e)}
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Requirement organization failed. Please try again."
        )


@router.post("/apply-suggestion")
async def apply_suggestion(
    request: ApplySuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Apply AI suggestion to update requirement text.
    Implements REQ_17, BR-14: State Consistency, BR-15: Undo Log.
    Includes input validation and access control.
    """
    try:
        logger.info(
            f"Applying suggestion for req_id={request.req_id}",
            extra={"user_id": current_user.user_id}
        )

        # Retrieve requirement with ownership validation
        req_res = await db.execute(
            select(Requirement).filter(Requirement.req_id == request.req_id)
        )
        req = req_res.scalar_one_or_none()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found"
            )

        # Verify user has access to this requirement
        doc_res = await db.execute(
            select(RequirementDocument).filter(RequirementDocument.doc_id == req.doc_id)
        )
        doc = doc_res.scalar_one_or_none()

        if not doc or doc.uploaded_by != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found or access denied"
            )

        # Validate input
        if not request.new_text or request.new_text.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New text cannot be empty"
            )

        if request.new_text.strip() == req.current_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New text is the same as current text"
            )

        # Store old text for undo functionality
        old_text = req.current_text

        # Create version history entry
        try:
            from backend.models.validation import RequirementVersionHistory
            version_entry = RequirementVersionHistory(
                req_id=request.req_id,
                doc_id=req.doc_id,
                project_id=req.project_id,
                old_text=old_text,
                new_text=request.new_text,
                change_reason="AI suggestion applied",
                changed_by=current_user.user_id,
                change_type="suggestion_applied"
            )
            db.add(version_entry)
            logger.info(f"Created version history entry for req_id={request.req_id}")
        except ImportError:
            req.previous_text = old_text
            logger.info("Using simple previous_text backup for undo functionality")

        # Update requirement with new text
        req.current_text = request.new_text
        req.last_modified_by = current_user.user_id
        req.last_modified_at = datetime.now(timezone.utc)

        # Mark associated defects as suggestion_applied
        from backend.models.validation import Defect
        await db.execute(
            update(Defect)
            .filter(Defect.req_id == request.req_id)
            .values(
                suggestion_applied=1,
                applied_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        )

        await db.commit()
        logger.info(f"Successfully applied suggestion for req_id={request.req_id}")

        return {
            "success": True,
            "req_id": request.req_id,
            "old_text": old_text,
            "new_text": request.new_text,
            "message": "Suggestion applied successfully",
            "version_history_created": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Failed to apply suggestion for req_id={request.req_id}",
            extra={"req_id": request.req_id, "user_id": current_user.user_id, "error": str(e)}
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply suggestion. Please try again."
        )


@router.post("/undo")
async def undo_suggestion(
    request: UndoSuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Undo last applied suggestion by reverting to previous text.
    Implements BR-15: Undo Log with version history support.
    Includes input validation and access control.
    """
    try:
        logger.info(
            f"Undoing suggestion for req_id={request.req_id}",
            extra={"user_id": current_user.user_id}
        )

        # Retrieve requirement with ownership validation
        req_res = await db.execute(
            select(Requirement).filter(Requirement.req_id == request.req_id)
        )
        req = req_res.scalar_one_or_none()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found"
            )

        doc_res = await db.execute(
            select(RequirementDocument).filter(RequirementDocument.doc_id == req.doc_id)
        )
        doc = doc_res.scalar_one_or_none()

        if not doc or doc.uploaded_by != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found or access denied"
            )

        # Try to get previous version from version history
        previous_text = None

        try:
            from backend.models.validation import RequirementVersionHistory
            version_res = await db.execute(
                select(RequirementVersionHistory)
                .filter(RequirementVersionHistory.req_id == request.req_id)
                .order_by(RequirementVersionHistory.created_at.desc())
            )
            version_entry = version_res.scalar_one_or_none()

            if version_entry:
                previous_text = version_entry.old_text
                logger.info(f"Found previous version from history: {version_entry.version_id}")
                await db.delete(version_entry)
            else:
                previous_text = req.previous_text
                if previous_text:
                    req.previous_text = None

        except ImportError:
            previous_text = req.previous_text
            if previous_text:
                req.previous_text = None

        if not previous_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No previous version found to undo"
            )

        if previous_text == req.current_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current text is already the same as previous version"
            )

        # Create version history entry for undo action
        try:
            from backend.models.validation import RequirementVersionHistory
            undo_version = RequirementVersionHistory(
                req_id=request.req_id,
                doc_id=req.doc_id,
                project_id=req.project_id,
                old_text=req.current_text,
                new_text=previous_text,
                change_reason="Undo suggestion applied",
                changed_by=current_user.user_id,
                change_type="undo"
            )
            db.add(undo_version)
            logger.info(f"Created undo version history entry")
        except ImportError:
            req.previous_text = req.current_text

        # Revert to previous text
        current_text = req.current_text
        req.current_text = previous_text
        req.last_modified_by = current_user.user_id
        req.last_modified_at = datetime.now(timezone.utc)

        # Mark associated defects as suggestion_applied = 0 (restored)
        from backend.models.validation import Defect
        await db.execute(
            update(Defect)
            .filter(Defect.req_id == request.req_id)
            .values(
                suggestion_applied=0,
                applied_at=None
            )
        )

        await db.commit()
        logger.info(f"Successfully undone suggestion for req_id={request.req_id}")

        return {
            "success": True,
            "req_id": request.req_id,
            "old_text": current_text,
            "new_text": previous_text,
            "message": "Suggestion undone successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Failed to undo suggestion for req_id={request.req_id}",
            extra={"req_id": request.req_id, "user_id": current_user.user_id, "error": str(e)}
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to undo suggestion. Please try again."
        )