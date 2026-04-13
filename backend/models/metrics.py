"""ProjectMetrics model."""
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base
from models.user import _uuid, _now


class ProjectMetrics(Base):
    __tablename__ = "project_metrics"

    metrics_id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), unique=True, nullable=False)
    validation_id = Column(String, ForeignKey("validation_sessions.validation_id", ondelete="CASCADE"), nullable=False)
    complexity_score = Column(Float, nullable=True)
    actor_count = Column(Integer, nullable=False, default=0)
    total_requirements = Column(Integer, nullable=False, default=0)
    avg_requirement_words = Column(Float, nullable=True)
    workflow_depth = Column(Integer, nullable=False, default=0)
    estimated_weeks = Column(Float, nullable=True)
    relative_cost_index = Column(String, nullable=True)
    quality_score = Column(Float, nullable=True)
    validation_rate = Column(Float, nullable=True)
    modal_density = Column(Float, nullable=True)
    vague_density = Column(Float, nullable=True)
    calculated_at = Column(String, nullable=False, default=_now)

    project = relationship("Project", back_populates="metrics")
    validation_session = relationship("ValidationSession", back_populates="metrics")
