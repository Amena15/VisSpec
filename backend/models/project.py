"""Project model."""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base
from models.user import _uuid, _now


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

    owner = relationship("User", back_populates="projects")
    documents = relationship("RequirementDocument", back_populates="project", cascade="all, delete-orphan")
    validation_sessions = relationship("ValidationSession", back_populates="project", cascade="all, delete-orphan")
    diagrams = relationship("Diagram", back_populates="project", cascade="all, delete-orphan")
    metrics = relationship("ProjectMetrics", back_populates="project", uselist=False, cascade="all, delete-orphan")
    traceability_matrix = relationship("TraceabilityMatrix", back_populates="project", cascade="all, delete-orphan")
    traceability_notes = relationship("TraceabilityNote", back_populates="project", cascade="all, delete-orphan")
    review_audits = relationship("ReviewAudit", back_populates="project", cascade="all, delete-orphan")
    export_reports = relationship("ExportReport", back_populates="project", cascade="all, delete-orphan")
