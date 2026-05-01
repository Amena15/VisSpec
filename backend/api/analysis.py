from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import json
from datetime import datetime

from models.user import User
from models.project import Project
from models.requirement import Requirement
from models.document import RequirementDocument
from schemas.analysis import (
    SemanticAnalysisRequest, 
    SemanticAnalysisResponse,
    PredictiveAnalysisRequest,
    PredictiveAnalysisResponse,
    AnalysisResult as AnalysisResultSchema
)
from services.ai.semantic_analyzer import SemanticAnalyzer
from services.ai.predictive_analyzer import PredictiveAnalyzer
from services.ai.requirement_organizer import requirement_organizer
from utils.security import get_current_active_user
from config.database import get_db
from core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Initialize AI services
semantic_analyzer = SemanticAnalyzer()
predictive_analyzer = PredictiveAnalyzer()


@router.post("/semantic", response_model=SemanticAnalysisResponse)
def analyze_semantic(
    request: SemanticAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Perform semantic analysis on text using spaCy and LLaMA 3
    """
    try:
        result = semantic_analyzer.analyze_text(request.text)

        return SemanticAnalysisResponse(
            id="semantic_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            text=request.text,
            entities=result.get("entities", []),
            relations=result.get("relations", []),
            ambiguities=result.get("ambiguities", []),
            confidence_score=result.get("confidence_score", 0.0),
            processed_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic analysis failed: {str(e)}"
        )


@router.post("/predictive", response_model=PredictiveAnalysisResponse)
def analyze_predictive(
    request: PredictiveAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Perform predictive analysis to estimate complexity and effort.
    Implements REQ_14 and REQ_15 exactly as specified in FYP report.
    """
    try:
        result = predictive_analyzer.analyze_text(request.text)

        return PredictiveAnalysisResponse(
            id="predictive_" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            text=request.text,
            complexity_score=result.get("complexity_score", 0),
            estimated_effort_weeks=result.get("estimated_effort_weeks", 0.0),
            cost_index=result.get("cost_index", "low"),
            risk_level=result.get("risk_level", "unknown"),
            recommendations=result.get("recommendations", []),
            confidence_score=result.get("confidence_score", 0.0),
            complexity_breakdown=result.get("complexity_breakdown"),
            processed_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Predictive analysis failed: {str(e)}"
        )


@router.post("/full", response_model=AnalysisResultSchema)
def analyze_full(
    semantic_request: SemanticAnalysisRequest,
    predictive_request: PredictiveAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Perform both semantic and predictive analysis
    """
    try:
        # Perform semantic analysis
        semantic_result = semantic_analyzer.analyze_text(semantic_request.text)
        semantic_response = SemanticAnalysisResponse(
            id="temp_semantic",
            text=semantic_request.text,
            entities=semantic_result.get("entities", []),
            relations=semantic_result.get("relations", []),
            ambiguities=semantic_result.get("ambiguities", []),
            confidence_score=semantic_result.get("confidence_score", 0.0),
            processed_at=datetime.utcnow()
        )

        # Perform predictive analysis
        predictive_result = predictive_analyzer.analyze_text(predictive_request.text)
        predictive_response = PredictiveAnalysisResponse(
            id="temp_predictive",
            text=predictive_request.text,
            complexity_score=predictive_result.get("complexity_score", 0),
            estimated_effort_weeks=predictive_result.get("estimated_effort_weeks", 0.0),
            cost_index=predictive_result.get("cost_index", "low"),
            risk_level=predictive_result.get("risk_level", "unknown"),
            recommendations=predictive_result.get("recommendations", []),
            confidence_score=predictive_result.get("confidence_score", 0.0),
            complexity_breakdown=predictive_result.get("complexity_breakdown"),
            processed_at=datetime.utcnow()
        )

        # Calculate overall confidence (average of semantic + predictive confidence)
        predictive_confidence = predictive_response.confidence_score
        overall_confidence = round(
            (semantic_response.confidence_score + predictive_confidence) / 2,
            2,
        )
        
        return AnalysisResultSchema(
            semantic_analysis=semantic_response,
            predictive_analysis=predictive_response,
            overall_confidence=overall_confidence,
            generated_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Full analysis failed: {str(e)}"
        )


@router.post("/enrich/{doc_id}")
def enrich_requirements(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Organize, classify, and enrich requirements for a document.
    
    This endpoint runs AFTER document upload and decouples the heavy
    LLM processing from the HTTP upload request to prevent timeouts.
    
    Steps:
    1. Retrieve raw requirements from DB
    2. Call requirement_organizer to:
       - Group into modules
       - Generate semantic IDs (FR-UM-01, NFR-SEC-01)
       - Standardize text format
       - Classify by category
       - Extract actors, modal verbs, vague terms
    3. Update each Requirement record in DB
    4. Return enriched requirements
    """
    try:
        # ------------------------------------------------------------------
        # 1. Retrieve document and requirements
        # ------------------------------------------------------------------
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
                detail="Document not found or access denied",
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

        # Build raw requirements list for organizer
        raw_reqs = [
            {
                "req_id": r.req_id,
                "req_identifier": r.req_identifier,
                "section_header": r.section_header,
                "original_text": r.original_text,
                "current_text": r.current_text,
                "word_count": r.word_count,
                "sequence_order": r.sequence_order,
            }
            for r in requirements
        ]

        # Get full document text for professional extraction
        full_text = doc.content or ""
        
        # ------------------------------------------------------------------
        # 2. Run professional requirement extraction
        # ------------------------------------------------------------------
        logger.info(f"Starting professional requirement extraction for doc_id={doc_id}")
        
        # Use professional extraction first (from full document text)
        professional_reqs = requirement_organizer.extract_professional_requirements(
            full_text=full_text,
            use_llm=True,
        )
        
        # If professional extraction worked, use those results
        if professional_reqs:
            enriched_reqs = professional_reqs
            logger.info(f"Professional extraction successful for doc_id={doc_id}, extracted {len(enriched_reqs)} requirements")
        else:
            # Fallback to traditional organization
            full_text = "\n\n".join(r.original_text for r in requirements)
            enriched_reqs = requirement_organizer.organize_and_enrich(
                requirements=raw_reqs,
                full_text=full_text,
                use_llm=True,
            )
            logger.info(f"Fallback to traditional organization for doc_id={doc_id}, processed {len(enriched_reqs)} requirements")
        logger.info(f"Enrichment complete for doc_id={doc_id}, processed {len(enriched_reqs)} requirements")

        # ------------------------------------------------------------------
        # 3. Update Requirement records in DB
        # ------------------------------------------------------------------
        updated_count = 0
        for enriched in enriched_reqs:
            req_id = enriched.get("req_id")
            if not req_id:
                continue

            req = db.query(Requirement).filter(Requirement.req_id == req_id).first()
            if not req:
                continue

            req.semantic_id = enriched.get("semantic_id")
            req.module_name = enriched.get("module_name")
            req.category = enriched.get("category")
            req.category_confidence = enriched.get("category_confidence")
            req.actors_json = json.dumps(enriched.get("actors", []))
            req.modal_verbs_json = json.dumps(enriched.get("modal_verbs", []))
            req.vague_terms_json = json.dumps(enriched.get("vague_terms", []))
            
            # Update current_text if standardized
            if enriched.get("original_text") != req.original_text:
                req.current_text = enriched.get("original_text", req.current_text)

            updated_count += 1

        db.commit()
        logger.info(f"Updated {updated_count} requirements in DB for doc_id={doc_id}")

        # ------------------------------------------------------------------
        # 4. Build response
        # ------------------------------------------------------------------
        result_requirements = []
        for r in enriched_reqs:
            result_requirements.append({
                "req_id": r.get("req_id"),
                "req_identifier": r.get("req_identifier"),
                "semantic_id": r.get("semantic_id"),
                "section_header": r.get("section_header"),
                "module_name": r.get("module_name"),
                "original_text": r.get("original_text"),
                "current_text": r.get("current_text"),
                "word_count": r.get("word_count"),
                "category": r.get("category"),
                "category_confidence": r.get("category_confidence"),
                "actors": r.get("actors", []),
                "modal_verbs": r.get("modal_verbs", []),
                "vague_terms": r.get("vague_terms", []),
                "sequence_order": r.get("sequence_order"),
            })

        return {
            "doc_id": doc_id,
            "status": "completed",
            "total_requirements": len(result_requirements),
            "updated_count": updated_count,
            "requirements": result_requirements,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enrichment failed for doc_id={doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Requirement enrichment failed: {str(e)}"
        )
