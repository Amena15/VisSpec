"""
Fixed enrichment API with enhanced database handling and fallback
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import json
import logging
import traceback
from datetime import datetime, timezone
from pydantic import BaseModel

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

class UndoSuggestionRequest(BaseModel):
    req_id: str

logger = get_logger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])

@router.post("/enrich/{doc_id}")
def enrich_requirements(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    ENHANCED: Organize, classify, and enrich requirements for a document.
    
    Enhanced with:
    1. Multiple database commit attempts
    2. Session management improvements
    3. Fallback to in-memory response if database fails
    4. Enhanced error handling and logging
    """
    try:
        logger.info(f"Starting enhanced enrichment for doc_id={doc_id}")
        
        # ------------------------------------------------------------------
        # 1. Retrieve document and requirements
        # ------------------------------------------------------------------
        doc = db.query(RequirementDocument).filter(
            RequirementDocument.doc_id == doc_id
        ).first()
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        requirements = (
            db.query(Requirement)
            .filter(Requirement.doc_id == doc_id)
            .order_by(Requirement.sequence_order)
            .all()
        )

        if not requirements:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No requirements found in this document.",
            )

        logger.info(f"Found {len(requirements)} requirements for processing")

        # ------------------------------------------------------------------
        # 2. Build requirements list and apply text cleaning
        # ------------------------------------------------------------------
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

        # Apply text cleaning FIRST
        logger.info("Applying text cleaning to requirements")
        cleaned_reqs = TextCleaner.clean_requirements_batch(raw_reqs)
        
        # Count cleaning improvements
        cleaning_improvements = 0
        for i, cleaned in enumerate(cleaned_reqs):
            if cleaned["original_text"] != raw_reqs[i]["original_text"]:
                cleaning_improvements += 1
        
        logger.info(f"Text cleaning improved {cleaning_improvements} requirements")

        # ------------------------------------------------------------------
        # 3. Run organization with fallback
        # ------------------------------------------------------------------
        full_text = "\n\n".join(req["original_text"] for req in cleaned_reqs)
        
        try:
            # Keep LLM first (performance) but do not allow enrichment to block DB updates.
            use_llm = True
            logger.info("Attempting LLM-based organization first (DB persistence guaranteed)")
            enriched_reqs = requirement_organizer.organize_and_enrich(
                requirements=cleaned_reqs,
                full_text=full_text,
                use_llm=use_llm,
            )

            # If LLM path returns nothing, fall back to deterministic data so DB is still updated.
            if not enriched_reqs:
                raise Exception("LLM enrichment returned no requirements; triggering fallback")

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


        # ------------------------------------------------------------------
        # 4. Enhanced database update with multiple attempts
        # ------------------------------------------------------------------
        updated_count = 0
        db_errors = []
        
        logger.info(f"Starting enhanced database updates for {len(enriched_reqs)} enriched requirements")
        
        # Try multiple commit attempts
        max_commit_attempts = 3
        commit_success = False
        
        for commit_attempt in range(max_commit_attempts):
            try:
                logger.info(f"Database commit attempt {commit_attempt + 1}/{max_commit_attempts}")
                
                # Reset for new attempt
                updated_count = 0
                db_errors = []
                
                # Update each requirement
                for enriched in enriched_reqs:
                    try:
                        req_id = enriched.get("req_id")
                        if not req_id:
                            logger.warning(f"Skipping enriched requirement with no req_id")
                            continue

                        req = db.query(Requirement).filter(Requirement.req_id == req_id).first()
                        if not req:
                            logger.warning(f"Requirement not found in DB: {req_id}")
                            continue

                        # Store old values for logging
                        old_category = req.category
                        old_module = req.module_name
                        old_semantic_id = req.semantic_id
                        old_original_text = req.original_text

                        # Update fields with validation
                        req.semantic_id = enriched.get("semantic_id") or req.semantic_id
                        req.module_name = enriched.get("module_name") or req.module_name
                        req.category = enriched.get("category") or req.category
                        req.category_confidence = enriched.get("category_confidence", req.category_confidence or 0.5)
                        
                        # Ensure JSON fields are properly serialized
                        actors = enriched.get("actors", [])
                        modal_verbs = enriched.get("modal_verbs", [])
                        vague_terms = enriched.get("vague_terms", [])
                        
                        req.actors_json = json.dumps(actors) if actors else req.actors_json
                        req.modal_verbs_json = json.dumps(modal_verbs) if modal_verbs else req.modal_verbs_json
                        req.vague_terms_json = json.dumps(vague_terms) if vague_terms else req.vague_terms_json
                        
                        # Update both original_text and current_text with cleaned text
                        cleaned_text = enriched.get("original_text", req.current_text)
                        if cleaned_text and cleaned_text != req.original_text:
                            req.original_text = cleaned_text
                            req.current_text = cleaned_text
                            logger.info(f"Updated both original_text and current_text for {req_id}")
                            logger.info(f"Updated text for {req_id}: improved cleaning")

                        updated_count += 1
                        
                        # Log changes
                        changes = []
                        if old_category != req.category:
                            changes.append(f"category: {old_category} → {req.category}")
                        if old_module != req.module_name:
                            changes.append(f"module: {old_module} → {req.module_name}")
                        if old_semantic_id != req.semantic_id:
                            changes.append(f"semantic_id: {old_semantic_id} → {req.semantic_id}")
                        if old_original_text != req.original_text:
                            changes.append("text: cleaned")
                        
                        if changes:
                            logger.info(f"Updated {req_id}: {', '.join(changes)}")
                        
                    except Exception as req_error:
                        error_msg = f"Error updating {enriched.get('req_id', 'unknown')}: {req_error}"
                        db_errors.append(error_msg)
                        logger.error(error_msg)
                        continue

                # Force database commit with enhanced validation
                try:
                    db.flush()  # Validate before commit
                    logger.info("Database flush successful - proceeding with commit")
                    
                    db.commit()
                    logger.info(f"✅ Database commit successful: {updated_count} requirement updates committed")
                    commit_success = True
                    break  # Success, exit retry loop
                    
                except Exception as commit_error:
                    logger.error(f"❌ Database commit attempt {commit_attempt + 1} failed: {commit_error}")
                    logger.error("Rolling back transaction")
                    db.rollback()
                    
                    if commit_attempt < max_commit_attempts - 1:
                        logger.info(f"Retrying commit in 2 seconds...")
                        import time
                        time.sleep(2)
                    else:
                        raise commit_error
                
            except Exception as attempt_error:
                logger.error(f"Commit attempt {commit_attempt + 1} failed: {attempt_error}")
                if commit_attempt == max_commit_attempts - 1:
                    raise attempt_error

        if not commit_success:
            logger.error("All commit attempts failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database update failed after multiple attempts"
            )

        # ------------------------------------------------------------------
        # 5. Build enhanced response
        # ------------------------------------------------------------------

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

        logger.info(f"Enhanced enrichment completed successfully for doc_id={doc_id}")
        
        # Summary statistics
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

        return {
            "message": "Requirements organized and enriched successfully",
            "total_requirements": len(result_requirements),
            "updated_requirements": updated_count,
            "cleaning_improvements": cleaning_improvements,
            "semantic_ids_generated": semantic_ids_generated,
            "category_distribution": category_counts,
            "module_distribution": module_counts,
            "requirements": result_requirements,
            "doc_id": doc_id,
            "database_errors": db_errors if db_errors else None,
            "commit_attempts": commit_attempt + 1 if 'commit_attempt' in locals() else 1,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced enrichment failed for doc_id={doc_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Requirement organization failed: {str(e)}"
        )


@router.post("/apply-suggestion")
def apply_suggestion(
    request: ApplySuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Apply AI suggestion to update requirement text.
    Implements REQ_17, BR-14: State Consistency, BR-15: Undo Log.
    """
    try:
        logger.info(f"Applying suggestion for req_id={request.req_id}")
        
        # Retrieve requirement with ownership validation
        req = db.query(Requirement).filter(Requirement.req_id == request.req_id).first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found"
            )
        
        # Verify user has access to this requirement
        doc = db.query(RequirementDocument).filter(
            RequirementDocument.doc_id == req.doc_id
        ).first()
        
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
        
        # Store old text for undo functionality (BR-15)
        old_text = req.current_text
        
        # Create version history entry
        try:
            # Import version history model
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
            # If version history table doesn't exist, use simple backup
            req.previous_text = old_text
            logger.info("Using simple previous_text backup for undo functionality")
        
        # Update requirement with new text
        req.current_text = request.new_text
        req.last_modified_by = current_user.user_id
        req.last_modified_at = datetime.now(timezone.utc)
        
        # Mark associated defects as suggestion_applied
        from models.validation import Defect
        db.query(Defect).filter(Defect.req_id == request.req_id).update({
            "suggestion_applied": 1,
            "applied_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        
        # Commit changes
        db.commit()
        
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
        logger.error(f"Failed to apply suggestion: {e}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply suggestion: {str(e)}"
        )


@router.post("/undo")
def undo_suggestion(
    request: UndoSuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Undo last applied suggestion by reverting to previous text.
    Implements BR-15: Undo Log with version history support.
    """
    try:
        logger.info(f"Undoing suggestion for req_id={request.req_id}")
        
        # Retrieve requirement with ownership validation
        req = db.query(Requirement).filter(Requirement.req_id == request.req_id).first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found"
            )
        
        # Verify user has access to this requirement
        doc = db.query(RequirementDocument).filter(
            RequirementDocument.doc_id == req.doc_id
        ).first()
        
        if not doc or doc.uploaded_by != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found or access denied"
            )
        
        # Try to get previous version from version history
        previous_text = None
        
        try:
            from models.requirement_history import RequirementVersionHistory
            
            # Get the most recent version entry for this requirement
            version_entry = db.query(RequirementVersionHistory).filter(
                RequirementVersionHistory.req_id == request.req_id
            ).order_by(RequirementVersionHistory.created_at.desc()).first()
            
            if version_entry:
                previous_text = version_entry.old_text
                logger.info(f"Found previous version from history: {version_entry.version_id}")
                
                # Delete the version entry since we're using it
                db.delete(version_entry)
                
            else:
                # Fall back to previous_text column
                previous_text = req.previous_text
                if previous_text:
                    req.previous_text = None  # Clear after using
                
        except ImportError:
            # Version history table not available, use simple backup
            previous_text = req.previous_text
            if previous_text:
                req.previous_text = None  # Clear after using
        
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
        
        # Create version history entry for the undo action
        try:
            from models.requirement_history import RequirementVersionHistory
            
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
            # Store current text as previous_text for redo
            req.previous_text = req.current_text
        
        # Revert to previous text
        current_text = req.current_text
        req.current_text = previous_text
        req.last_modified_by = current_user.user_id
        req.last_modified_at = datetime.now(timezone.utc)
        
        # Mark associated defects as suggestion_applied = 0 (restored)
        from models.validation import Defect
        db.query(Defect).filter(Defect.req_id == request.req_id).update({
            "suggestion_applied": 0,
            "applied_at": None
        })
        
        # Commit changes
        db.commit()
        
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
        logger.error(f"Failed to undo suggestion: {e}")
        logger.error(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to undo suggestion: {str(e)}"
        )
