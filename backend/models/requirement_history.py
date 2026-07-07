"""Requirement version history model for BR-15 compliance."""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.models.user import _uuid
from datetime import datetime, timezone

def _now_dt():
    return datetime.now(timezone.utc)

class RequirementVersionHistory(Base):
    __tablename__ = "requirement_version_history"

    version_id = Column(String, primary_key=True, default=_uuid)
    req_id = Column(String, ForeignKey("requirements.req_id", ondelete="CASCADE"), nullable=False, index=True)
    doc_id = Column(String, ForeignKey("requirement_documents.doc_id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    old_text = Column(Text, nullable=False)
    new_text = Column(Text, nullable=False)
    change_reason = Column(String(255), nullable=True)
    changed_by = Column(String, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    change_type = Column(String(50), nullable=False, default="suggestion_applied")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now_dt)

    # Relationships
    requirement = relationship("Requirement", back_populates="version_history")
    document = relationship("RequirementDocument")
    project = relationship("Project")
    changed_by_user = relationship("backend.models.user.User", foreign_keys=[changed_by], viewonly=True)