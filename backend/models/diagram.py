"""
Diagram and DiagramElement models with IEEE compliance.
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.models.user import _uuid, _now


class Diagram(Base):
    __tablename__ = "diagrams"

    diagram_id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    validation_id = Column(String, ForeignKey("validation_sessions.validation_id", ondelete="CASCADE"), nullable=True)
    diagram_type = Column(String, nullable=False, index=True)  # usecase, sequence, activity
    scenario_name = Column(String, nullable=True)
    
    # Store both formats
    mermaid_syntax = Column(Text, nullable=False)
    plantuml_syntax = Column(Text, nullable=True)

    # Compliance flags
    syntax_valid = Column(Integer, nullable=False, default=0)
    total_elements = Column(Integer, nullable=False, default=0)
    hallucination_rejected_count = Column(Integer, nullable=False, default=0)
    generation_time_ms = Column(Integer, nullable=True)
    created_at = Column(String, nullable=False, default=_now)

    # Relationships
    project = relationship("Project", back_populates="diagrams")
    validation_session = relationship("ValidationSession", back_populates="diagrams")
    elements = relationship("DiagramElement", back_populates="diagram", cascade="all, delete-orphan")


class DiagramElement(Base):
    __tablename__ = "diagram_elements"

    element_id = Column(String, primary_key=True, default=_uuid)
    diagram_id = Column(String, ForeignKey("diagrams.diagram_id", ondelete="CASCADE"), nullable=False, index=True)
    source_req_id = Column(String, ForeignKey("requirements.req_id", ondelete="CASCADE"), nullable=True, index=True)
    element_type = Column(String, nullable=False)  # actor, usecase, participant, message, activity
    element_name = Column(String, nullable=False)
    was_hallucination = Column(Integer, nullable=False, default=0)  # BR-11: No hallucinated actors
    created_at = Column(String, nullable=False, default=_now)

    diagram = relationship("Diagram", back_populates="elements")
    source_requirement = relationship("Requirement", back_populates="diagram_elements")