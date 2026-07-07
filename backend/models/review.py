"""ReviewAudit model."""
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.models.user import _uuid, _now



class ReviewAudit(Base):
    __tablename__ = "review_audits"

    review_id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    supervisor_id = Column(String, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    validation_id = Column(String, ForeignKey("validation_sessions.validation_id", ondelete="SET NULL"), nullable=True)
    decision = Column(String, nullable=False, default="pending")
    comments = Column(Text, nullable=True)
    quality_score_at_review = Column(Float, nullable=True)
    defect_count_at_review = Column(Integer, nullable=True)
    review_in_progress = Column(Integer, nullable=False, default=0)
    review_started_at = Column(String, nullable=True)
    review_completed_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False, default=_now)

    project = relationship("Project", back_populates="review_audits")
    supervisor = relationship("backend.models.user.User", viewonly=True)
    validation_session = relationship("ValidationSession", back_populates="review_audits")
