"""Traceability schemas."""
from pydantic import BaseModel
from typing import Optional, List


class TraceabilityEntry(BaseModel):
    matrix_id: str
    project_id: str
    req_id: str
    validation_id: Optional[str] = None
    diagram_id: Optional[str] = None
    validation_status: str = "pending"
    defect_types_json: Optional[str] = None
    linked_diagram_elements_json: Optional[str] = None
    updated_at: str

    class Config:
        from_attributes = True


class TraceabilityNoteCreate(BaseModel):
    req_id: str
    project_id: str
    content: str
    note_type: str = "user_annotation"


class TraceabilityNoteResponse(BaseModel):
    note_id: str
    req_id: str
    project_id: str
    content: str
    note_type: str
    is_resolved: int
    created_at: str

    class Config:
        from_attributes = True
