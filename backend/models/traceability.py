"""TraceabilityMatrix and TraceabilityNote models."""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.models.user import _uuid, _now



class TraceabilityMatrix(Base):
    __tablename__ = "traceability_matrix"
    __table_args__ = {"extend_existing": True}

    matrix_id = Column(String, primary_key=True, default=_uuid)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    req_id = Column(String, ForeignKey("requirements.req_id", ondelete="CASCADE"), nullable=False, index=True)
    validation_id = Column(String, ForeignKey("validation_sessions.validation_id", ondelete="SET NULL"), nullable=True)
    diagram_id = Column(String, ForeignKey("diagrams.diagram_id", ondelete="SET NULL"), nullable=True)
    validation_status = Column(String, nullable=False, default="pending")
    defect_types_json = Column(Text, nullable=True)
    linked_diagram_elements_json = Column(Text, nullable=True)
    updated_at = Column(String, nullable=False, default=_now)

    project = relationship("Project", back_populates="traceability_matrix")
    requirement = relationship("Requirement", back_populates="traceability_matrix")
    validation_session = relationship("ValidationSession", back_populates="traceability_matrix")


class TraceabilityNote(Base):
    __tablename__ = "traceability_notes"
    __table_args__ = {"extend_existing": True}

    note_id = Column(String, primary_key=True, default=_uuid)
    req_id = Column(String, ForeignKey("requirements.req_id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    note_type = Column(String, nullable=False, default="user_annotation")
    is_resolved = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, default=_now)

    requirement = relationship("Requirement", back_populates="traceability_notes")
    creator = relationship("User", back_populates="traceability_notes")
    project = relationship("Project", back_populates="traceability_notes")
