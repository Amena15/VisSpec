"""PasswordResetToken, SystemLog, AIPromptLog, ExportReport models."""
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.models.user import _uuid, _now



class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token_id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(String, nullable=False)
    is_used = Column(Integer, nullable=False, default=0)
    previous_hash_check = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=_now)

    user = relationship("User")


class SystemLog(Base):
    __tablename__ = "system_logs"

    log_id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    level = Column(String, nullable=False, index=True)
    event = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, default=_now, index=True)

    user = relationship("User")


class AIPromptLog(Base):
    __tablename__ = "ai_prompt_logs"

    prompt_log_id = Column(String, primary_key=True, default=_uuid)
    validation_id = Column(String, ForeignKey("validation_sessions.validation_id", ondelete="CASCADE"), nullable=False)
    req_batch_index = Column(Integer, nullable=False)
    model = Column(String, nullable=False)
    temperature = Column(Float, nullable=False, default=0.1)
    response_time_ms = Column(Integer, nullable=True)
    was_retry = Column(Integer, nullable=False, default=0)
    parse_succeeded = Column(Integer, nullable=False)
    created_at = Column(String, nullable=False, default=_now)

    validation_session = relationship("ValidationSession", back_populates="ai_prompt_logs")


class ExportReport(Base):
    __tablename__ = "export_reports"

    report_id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    validation_id = Column(String, ForeignKey("validation_sessions.validation_id", ondelete="CASCADE"), nullable=False)
    generated_by = Column(String, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    report_type = Column(String, nullable=False, default="full")
    includes_diagrams = Column(Integer, nullable=False, default=1)
    includes_metrics = Column(Integer, nullable=False, default=1)
    includes_traceability = Column(Integer, nullable=False, default=1)
    watermark_text = Column(String, nullable=False, default="VisSpec")
    file_size_bytes = Column(Integer, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)
    generated_at = Column(String, nullable=False, default=_now)

    project = relationship("Project", back_populates="export_reports")
    validation_session = relationship("ValidationSession", back_populates="export_reports")
    generated_by_user = relationship("User", back_populates="export_reports")
