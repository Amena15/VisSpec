"""Project model."""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.models.user import _uuid, _now



class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String, primary_key=True, default=_uuid)
    owner_id = Column(String, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending", index=True)
    review_status = Column(String, nullable=False, default="not_reviewed")
    is_deleted = Column(Integer, nullable=False, default=0)
    deleted_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=_now)
    updated_at = Column(String, nullable=False, default=_now, onupdate=_now)

    owner = relationship("backend.models.user.User", viewonly=True)
    documents = relationship("backend.models.document.RequirementDocument", back_populates="project", cascade="all, delete-orphan")
    validation_sessions = relationship("backend.models.validation.ValidationSession", back_populates="project", cascade="all, delete-orphan")
    diagrams = relationship("backend.models.diagram.Diagram", back_populates="project", cascade="all, delete-orphan")
    metrics = relationship("backend.models.metrics.ProjectMetrics", back_populates="project", uselist=False, cascade="all, delete-orphan")
    traceability_matrix = relationship("backend.models.traceability.TraceabilityMatrix", back_populates="project", cascade="all, delete-orphan")
    traceability_notes = relationship("backend.models.traceability.TraceabilityNote", back_populates="project", cascade="all, delete-orphan")
    review_audits = relationship("backend.models.review.ReviewAudit", back_populates="project", cascade="all, delete-orphan")
    export_reports = relationship("backend.models.auxiliary.ExportReport", back_populates="project", cascade="all, delete-orphan")