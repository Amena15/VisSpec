"""Validation request/response schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ValidationRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Requirements text to validate")


class DocumentValidationRequest(BaseModel):
    doc_id: str = Field(..., description="Document ID to validate")
    project_id: Optional[str] = Field(None, description="Optional project ID")


class DefectResponse(BaseModel):
    text: str
    type: str
    severity: str
    confidence: float
    description: str
    suggestion: Optional[str] = None
    req_id: Optional[str] = None


class ValidationResponse(BaseModel):
    overall_score: float
    total_defects: int
    defects_by_type: Dict[str, int]
    defects_by_severity: Dict[str, int]
    defects: List[DefectResponse]
    llm_used: bool
    processing_time_ms: int


class DocumentValidationResponse(BaseModel):
    validation_id: str
    doc_id: str
    project_id: Optional[str] = None
    status: str
    overall_score: Optional[float] = None
    total_defects: int = 0
    total_requirements: int = 0
    defects_by_type: Dict[str, int] = {}
    defects_by_severity: Dict[str, int] = {}
    defects: List[DefectResponse] = []
    llm_used: bool = False
    processing_time_ms: int = 0
    perfect_score: bool = False
    error_message: Optional[str] = None
