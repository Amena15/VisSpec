"""RequirementDocument model."""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.models.user import _uuid, _now

# Ensure relationships using string targets do not create duplicate ORM classes
# when modules are imported via different sys.path roots.




class RequirementDocument(Base):
    __tablename__ = "requirement_documents"
    __table_args__ = {"extend_existing": True}

    doc_id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(String, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    filename = Column(String, nullable=False)
    file_extension = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    word_count = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="Ready for Analysis", index=True)
    parse_error = Column(Text, nullable=True)
    is_scanned_pdf = Column(Integer, nullable=False, default=0)
    extracted_author = Column(String, nullable=True)
    extracted_version = Column(String, nullable=True)
    malware_scan_passed = Column(Integer, nullable=False, default=0)
    content = Column(LargeBinary, nullable=True)  # Store original uploaded file (binary)
    extracted_text = Column(Text, nullable=True)  # Sanitized text for full-text search indexing
    upload_date = Column(String, nullable=False, default=_now)

    project = relationship("backend.models.project.Project", back_populates="documents")
    uploader = relationship("backend.models.user.User", back_populates="uploaded_documents")
    requirements = relationship("Requirement", back_populates="document", cascade="all, delete-orphan", foreign_keys="Requirement.doc_id")
    validation_sessions = relationship("backend.models.validation.ValidationSession", back_populates="document", cascade="all, delete-orphan")
