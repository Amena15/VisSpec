from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

class DocumentBase(BaseModel):
    title: str
    content: str
    is_public: bool = False

class DocumentCreate(DocumentBase):
    pass

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