"""Schemas for semantic and predictive analysis."""
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class SemanticAnalysisRequest(BaseModel):
    """Request for semantic analysis of requirements text."""
    text: str
    analysis_type: str = "semantic"


class SemanticAnalysisResponse(BaseModel):
    """Response from semantic analysis."""
    id: str
    text: str
    entities: List[Dict]
    relations: List[Dict]
    ambiguities: List[Dict]
    confidence_score: float
    processed_at: datetime


class PredictiveAnalysisRequest(BaseModel):
    """Request for predictive analysis (complexity, effort, risk)."""
    text: str
    analysis_type: str = "predictive"


class PredictiveAnalysisResponse(BaseModel):
    """Response with complexity score, effort estimation, risk level."""
    id: str
    text: str
    complexity_score: int          # 0‑100 scale
    estimated_effort_weeks: float  # REQ‑15
    cost_index: str                # "low", "medium", "high"
    risk_level: str                # "low", "medium", "high", "very high"
    recommendations: List[str]
    confidence_score: float
    complexity_breakdown: Optional[Dict] = None
    processed_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "complexity_score": 65,
                "estimated_effort_weeks": 10.5,
                "cost_index": "high",
                "risk_level": "high",
                "confidence_score": 0.85
            }
        }


class AnalysisResult(BaseModel):
    """Combined result of both analyses."""
    semantic_analysis: Optional[SemanticAnalysisResponse] = None
    predictive_analysis: Optional[PredictiveAnalysisResponse] = None
    overall_confidence: float
    generated_at: datetime