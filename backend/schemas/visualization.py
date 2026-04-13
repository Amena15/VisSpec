from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Relationship(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    type: str  # "association", "include", "extend"

    class Config:
        populate_by_name = True

class VisualizationRequest(BaseModel):
    text: str
    diagram_type: str  # "usecase", "sequence", "activity", etc.
    options: Optional[Dict] = None

class VisualizationResponse(BaseModel):
    id: str
    diagram_type: str
    mermaid_syntax: str
    plantuml_syntax: str
    title: str
    description: str
    actors: List[str] = []
    use_cases: List[str] = []
    relationships: List[Relationship] = []
    generated_at: str