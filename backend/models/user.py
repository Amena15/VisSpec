"""User and UserRole model."""
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import relationship
from backend.config.database import Base
from enum import Enum as PyEnum
from passlib.context import CryptContext
import uuid
from datetime import datetime, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


class UserRole(PyEnum):
    ANALYST = "analyst"        # Regular user
    SUPERVISOR = "supervisor"  # Admin user


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}


    user_id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, index=True)
    is_pre_provisioned = Column(Integer, nullable=False, default=0)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(String, nullable=True)
    last_login_at = Column(String, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    storage_quota_mb = Column(Float, nullable=False, default=100)
    storage_used_bytes = Column(Integer, nullable=False, default=0)
    created_at = Column(String, nullable=False, default=_now)
    updated_at = Column(String, nullable=False, default=_now, onupdate=_now)

    # Relationships
    projects = relationship("backend.models.project.Project", viewonly=True)
    uploaded_documents = relationship("RequirementDocument", viewonly=True)
    validation_sessions = relationship("ValidationSession", viewonly=True)
    traceability_notes = relationship("TraceabilityNote", viewonly=True)
    review_audits = relationship("ReviewAudit", viewonly=True)
    export_reports = relationship("ExportReport", viewonly=True)

    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.password_hash)

    def set_password(self, password):
        truncated_password = password[:72] if len(password) > 72 else password
        self.password_hash = pwd_context.hash(truncated_password)
