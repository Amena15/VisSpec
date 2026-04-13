"""RequirementDocument model."""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base
from models.user import _uuid, _now


class RequirementDocument(Base):
    __tablename__ = "requirement_documents"

    doc_id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(String, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    filename = Column(String, nullable=False)
    file_extension = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    word_count = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="uploading", index=True)
    parse_error = Column(Text, nullable=True)
    is_scanned_pdf = Column(Integer, nullable=False, default=0)
    extracted_author = Column(String, nullable=True)
    extracted_version = Column(String, nullable=True)
    malware_scan_passed = Column(Integer, nullable=False, default=0)
    upload_date = Column(String, nullable=False, default=_now)

    project = relationship("Project", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")
    requirements = relationship("Requirement", back_populates="document", cascade="all, delete-orphan")
    validation_sessions = relationship("ValidationSession", back_populates="document", cascade="all, delete-orphan")
