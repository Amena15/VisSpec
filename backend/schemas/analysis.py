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
    complexity_score: int  # 0-100 scale - REQ_14
    estimated_effort_weeks: float  # REQ_15: duration in weeks
    cost_index: str  # "low", "medium", "high" - REQ_15
    risk_level: str  # "low", "medium", "high", "very high" - REQ_10
    recommendations: List[str]
    confidence_score: float
    complexity_breakdown: Optional[Dict] = None  # Transparency breakdown
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
    semantic_analysis: Optional[SemanticAnalysisResponse] = None
    predictive_analysis: Optional[PredictiveAnalysisResponse] = None
    overall_confidence: float
    generated_at: datetime