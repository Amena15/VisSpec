"""Validation request/response schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ValidationRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Requirements text to validate")


class DefectResponse(BaseModel):
    text: str
    type: str
    severity: str
    confidence: float
    description: str
    suggestion: Optional[str] = None


class ValidationResponse(BaseModel):
    overall_score: float
    total_defects: int
    defects_by_type: Dict[str, int]
    defects_by_severity: Dict[str, int]
    defects: List[DefectResponse]
    llm_used: bool
    processing_time_ms: int
