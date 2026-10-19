"""Validation session and defect models."""
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.models.user import _uuid, _now


def _default_llm_model() -> str:
    """Single source of truth: the configured LLM model id from settings.

    Kept as a zero-argument callable so SQLAlchemy evaluates it per-insert;
    this way the stored model id always matches backend/core/config.py.
    """
    try:
        from backend.core.config import settings
        return settings.llm_model_id
    except Exception:
        # Never hardcode a model id here — an unconfigured default is safer
        # than a stale one that would mislabel which model produced a result.
        return ""



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
    # Model actually used for this validation session. Single source of truth =
    # backend/core/config.py llm_model_id (profile-resolved; default profile
    # groq-gpt-oss-120b = openai/gpt-oss-120b via Groq); the Python-side
    # default is injected from settings at import time so this column can
    # never diverge from the configured model id.
    llm_model_used = Column(String, nullable=False, default=_default_llm_model)
    api_retries = Column(Integer, nullable=False, default=0)
    processing_time_ms = Column(Integer, nullable=True)
    # Note: Zero-retention is a policy guarantee of the LLM provider, not a
    # locally enforced code feature. Local PII redaction is applied in
    # backend/services/ai/privacy.py before text is sent to the provider.
    # This column is only an audit flag recording that LOCAL masking was
    # in effect (1=masking applied); it is NOT a provider guarantee claim.
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
