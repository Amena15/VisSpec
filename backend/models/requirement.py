"""Requirement model."""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.models.user import _uuid, _now



class Requirement(Base):
    __tablename__ = "requirements"
    __table_args__ = {"extend_existing": True}

    req_id = Column(String, primary_key=True, default=_uuid)
    doc_id = Column(String, ForeignKey("requirement_documents.doc_id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    req_identifier = Column(String, nullable=True)
    section_header = Column(String, nullable=True)
    original_text = Column(Text, nullable=False)
    current_text = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False, default=0)
    actors_json = Column(Text, nullable=True)
    modal_verbs_json = Column(Text, nullable=True)
    vague_terms_json = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True)
    category_confidence = Column(Float, nullable=True)
    semantic_id = Column(String, nullable=True)
    module_name = Column(String, nullable=True, index=True)
    validation_status = Column(String, nullable=False, default="pending", index=True)
    sequence_order = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, default=_now)

    document = relationship("backend.models.document.RequirementDocument", back_populates="requirements", foreign_keys=[doc_id])
    project = relationship("Project")
    defects = relationship("Defect", back_populates="requirement", cascade="all, delete-orphan")
    diagram_elements = relationship("DiagramElement", back_populates="source_requirement", cascade="all, delete-orphan")
    traceability_matrix = relationship("TraceabilityMatrix", back_populates="requirement", cascade="all, delete-orphan")
    traceability_notes = relationship("TraceabilityNote", back_populates="requirement", cascade="all, delete-orphan")
    version_history = relationship(
        "backend.models.requirement_history.RequirementVersionHistory",
        back_populates="requirement",
        cascade="all, delete-orphan"
    )