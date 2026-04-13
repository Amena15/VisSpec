from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class SemanticAnalysisRequest(BaseModel):
    text: str
    analysis_type: str = "semantic"  # "semantic", "predictive", etc.

class SemanticAnalysisResponse(BaseModel):
    id: str
    text: str
    entities: List[Dict]
    relations: List[Dict]
    ambiguities: List[Dict]
    confidence_score: float
    processed_at: datetime

class PredictiveAnalysisRequest(BaseModel):
    text: str
    analysis_type: str = "predictive"

class PredictiveAnalysisResponse(BaseModel):
    id: str
    text: str
    complexity_score: float
    estimated_effort_hours: float
    risk_level: str  # "low", "medium", "high"
    recommendations: List[str]
    confidence_score: float
    processed_at: datetime

class AnalysisResult(BaseModel):
    semantic_analysis: Optional[SemanticAnalysisResponse] = None
    predictive_analysis: Optional[PredictiveAnalysisResponse] = None
    overall_confidence: float
    generated_at: datetime