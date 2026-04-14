from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
from datetime import datetime

from models.user import User
from models import RequirementDocument
from schemas.analysis import (
    SemanticAnalysisRequest, 
    SemanticAnalysisResponse,
    PredictiveAnalysisRequest,
    PredictiveAnalysisResponse,
    AnalysisResult as AnalysisResultSchema
)
from services.ai.semantic_analyzer import SemanticAnalyzer
from services.ai.predictive_analyzer import PredictiveAnalyzer
from utils.security import get_current_active_user
from config.database import get_db

router = APIRouter()

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