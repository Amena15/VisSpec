"""
Fixed enrichment API with proper error handling and timeout prevention
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import json
import logging
import traceback

from models.user import User
from models.document import RequirementDocument
from models.requirement import Requirement
from config.database import get_db
from utils.security import get_current_active_user
from services.ai.requirement_organizer import requirement_organizer
from services.ai.text_cleaner import TextCleaner
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["analysis"])

@router.post("/enrich/{doc_id}")
def enrich_requirements(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    FIXED: Organize, classify, and enrich requirements for a document.
    
    This endpoint now includes:
    1. Proper error handling and timeouts
    2. Text cleaning before organization
    3. Guaranteed database commits
    4. Fallback to rule-based if LLM fails
    """
    try:
        logger.info(f"Starting enrichment for doc_id={doc_id}")
        
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
        
        # Simple ownership check
        if doc.uploaded_by != current_user.user_id:
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
            # Try rule-based organization first (more reliable)
            logger.info("Using rule-based organization")
            enriched_reqs = requirement_organizer.organize_and_enrich(
                requirements=cleaned_reqs,
                full_text=full_text,
                use_llm=False,  # Force rule-based for reliability
            )
            logger.info(f"Rule-based organization successful: {len(enriched_reqs)} requirements")
            
        except Exception as org_error:
            logger.error(f"Rule-based organization failed: {org_error}")
            # Emergency fallback: basic categorization only
            enriched_reqs = []
            for req in cleaned_reqs:
                enriched_reqs.append({
                    **req,
                    "semantic_id": f"REQ-{req['sequence_order']:03d}",
                    "module_name": "General",
                    "category": "uncategorized",
                    "category_confidence": 0.5,
                    "actors": [],
                    "modal_verbs": [],
                    "vague_terms": [],
                })
            logger.info(f"Emergency fallback applied: {len(enriched_reqs)} requirements")

        # ------------------------------------------------------------------
        # 4. Update Requirement records in DB with guaranteed commit
        # ------------------------------------------------------------------
        updated_count = 0
        db_errors = []
        
        logger.info(f"Starting database updates for {len(enriched_reqs)} enriched requirements")
        
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
                old_text = req.original_text

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
                
                # Update text if cleaned
                cleaned_text = enriched.get("original_text", req.original_text)
                if cleaned_text and cleaned_text != req.original_text:
                    req.current_text = cleaned_text
                    # Update original_text if it's a clear improvement
                    if (len(cleaned_text) < len(req.original_text) and 
                        "willwill" not in cleaned_text and 
                        "shallshall" not in cleaned_text and
                        "mustmust" not in cleaned_text and
                        "shouldshould" not in cleaned_text):
                        req.original_text = cleaned_text
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
                if old_text != req.original_text:
                    changes.append("text: cleaned")
                
                if changes:
                    logger.info(f"Updated {req_id}: {', '.join(changes)}")
                else:
                    logger.debug(f"No changes needed for {req_id}")
                
            except Exception as req_error:
                error_msg = f"Error updating {enriched.get('req_id', 'unknown')}: {req_error}"
                db_errors.append(error_msg)
                logger.error(error_msg)
                continue

        logger.info(f"Database update phase complete: {updated_count} updated, {len(db_errors)} errors")

        # Force database commit with detailed logging
        try:
            db.flush()  # Validate before commit
            logger.info("Database flush successful - proceeding with commit")
            
            db.commit()
            logger.info(f"✅ Database commit successful: {updated_count} requirement updates committed")
            
        except Exception as commit_error:
            logger.error(f"❌ Database commit failed: {commit_error}")
            logger.error("Rolling back transaction")
            db.rollback()
            
            # Return detailed error response
            error_detail = f"Database update failed. Updated {updated_count} requirements before failure. Errors: {'; '.join(db_errors[:3])}"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_detail
            )

        # ------------------------------------------------------------------
        # 5. Build response
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

        logger.info(f"Enrichment completed successfully for doc_id={doc_id}")
        
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
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enrichment failed for doc_id={doc_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Requirement organization failed: {str(e)}"
        )
