"""Document request/response schemas matching RequirementDocument model."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RequirementItem(BaseModel):
    """Individual requirement extracted from a document."""
    req_id: Optional[str] = None
    req_identifier: Optional[str] = None
    semantic_id: Optional[str] = None
    section_header: Optional[str] = None
    module_name: Optional[str] = None
    original_text: str
    current_text: Optional[str] = None
    word_count: int = 0
    category: Optional[str] = None
    category_confidence: Optional[float] = None
    actors: List[str] = []
    modal_verbs: List[str] = []
    vague_terms: List[str] = []
    sequence_order: int = 0
    validation_status: Optional[str] = "pending"

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    """Base document fields."""
    filename: str
    file_extension: str = Field(..., pattern=r"^(pdf|docx|txt)$")
    file_size_bytes: int = Field(..., le=10485760)  # 10MB max


class DocumentCreate(DocumentBase):
    """Schema for creating a new document record."""
    project_id: str


class DocumentUploadResponse(BaseModel):
    """Response returned after a successful document upload."""
    doc_id: str
    project_id: str
    filename: str
    file_extension: str
    file_size_bytes: int
    word_count: int
    page_count: Optional[int] = None
    status: str
    extracted_author: Optional[str] = None
    extracted_version: Optional[str] = None
    is_scanned_pdf: int = 0
    requirements_found: int = 0
    sections_found: List[str] = []
    upload_date: str

    class Config:
        from_attributes = True


class DocumentSummary(BaseModel):
    """Summary of a document for listing views."""
    doc_id: str
    project_id: str
    filename: str
    file_extension: str
    file_size_bytes: int
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    status: str
    requirements_found: int = 0
    upload_date: str

    class Config:
        from_attributes = True


class DocumentDetail(BaseModel):
    """Full document detail including extracted requirements."""
    doc_id: str
    project_id: str
    filename: str
    file_extension: str
    file_size_bytes: int
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    status: str
    parse_error: Optional[str] = None
    is_scanned_pdf: int = 0
    extracted_author: Optional[str] = None
    extracted_version: Optional[str] = None
    malware_scan_passed: int = 0
    upload_date: str
    requirements: List[RequirementItem] = []

    class Config:
        from_attributes = True


class DocumentDeleteResponse(BaseModel):
    """Response after deleting a document."""
    message: str
    doc_id: str
    deleted_requirements: int = 0
    deleted_validations: int = 0


# Legacy schemas kept for backward compatibility
class Document(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    analysis_result: Optional[str] = None
    visualization_data: Optional[str] = None
    is_public: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_public: Optional[bool] = None


class DocumentResponse(DocumentBase):
    id: int
    user_id: int
    analysis_result: Optional[str] = None
    visualization_data: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentInDB(DocumentResponse):
    hashed_content: Optional[str] = None
