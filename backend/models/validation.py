"""Validation session and defect models."""
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.models.user import _uuid, _now



class ValidationSession(Base):
    __tablename__ = "validation_sessions"
    __table_args__ = {"extend_existing": True}

    validation_id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    doc_id = Column(String, ForeignKey("requirement_documents.doc_id", ondelete="CASCADE"), nullable=False, index=True)
    triggered_by = Column(String, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    status = Column(String, nullable=False, default="running")
    overall_score = Column(Float, nullable=True)
    total_requirements = Column(Integer, nullable=False, default=0)
    defect_count = Column(Integer, nullable=False, default=0)
    ambiguity_count = Column(Integer, nullable=False, default=0)
    incompleteness_count = Column(Integer, nullable=False, default=0)
    inconsistency_count = Column(Integer, nullable=False, default=0)
    unverifiable_count = Column(Integer, nullable=False, default=0)
    llm_model_used = Column(String, nullable=False, default="llama3-70b-8192")
    api_retries = Column(Integer, nullable=False, default=0)
    processing_time_ms = Column(Integer, nullable=True)
    zero_retention_confirmed = Column(Integer, nullable=False, default=1)
    validation_date = Column(String, nullable=False, default=_now, index=True)
    error_message = Column(Text, nullable=True)

    project = relationship("backend.models.project.Project", back_populates="validation_sessions")
    document = relationship("backend.models.document.RequirementDocument", back_populates="validation_sessions")
    triggered_by_user = relationship("backend.models.user.User", viewonly=True)
    defects = relationship("backend.models.validation.Defect", back_populates="validation_session", cascade="all, delete-orphan")
    diagrams = relationship("backend.models.diagram.Diagram", back_populates="validation_session", cascade="all, delete-orphan")
    ai_prompt_logs = relationship("backend.models.auxiliary.AIPromptLog", back_populates="validation_session", cascade="all, delete-orphan")
    metrics = relationship("backend.models.metrics.ProjectMetrics", back_populates="validation_session", uselist=False, cascade="all, delete-orphan")
    traceability_matrix = relationship("backend.models.traceability.TraceabilityMatrix", back_populates="validation_session", cascade="all, delete-orphan")
    review_audits = relationship("backend.models.review.ReviewAudit", back_populates="validation_session", cascade="all, delete-orphan")
    export_reports = relationship("ExportReport", back_populates="validation_session")

class Defect(Base):
    __tablename__ = "defects"
    __table_args__ = {"extend_existing": True}

    defect_id = Column(String, primary_key=True, default=_uuid)
    validation_id = Column(String, ForeignKey("validation_sessions.validation_id", ondelete="CASCADE"), nullable=False, index=True)
    req_id = Column(String, ForeignKey("requirements.req_id", ondelete="CASCADE"), nullable=False, index=True)
    defect_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    ai_suggestion = Column(Text, nullable=True)
    suggestion_applied = Column(Integer, nullable=False, default=0)
    applied_at = Column(String, nullable=True)
    is_false_positive = Column(Integer, nullable=False, default=0)
    user_note = Column(Text, nullable=True)
    detected_at = Column(String, nullable=False, default=_now)

    validation_session = relationship("ValidationSession", back_populates="defects")
    requirement = relationship("Requirement", back_populates="defects")
