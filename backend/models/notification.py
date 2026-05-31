"""Notification model.

Used for notifying students about supervisor review decisions (BR-19).
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from config.database import Base
from models.user import _uuid


def _now():
    return datetime.now(timezone.utc).isoformat()


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)

    # e.g., review_approved, review_changes_requested
    type = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)

    is_read = Column(Boolean, nullable=False, default=False)

    created_at = Column(String, nullable=False, default=_now)

    # Relationships (optional but useful)
    # NOTE: User/Project relationships are not required for FK enforcement.
    # They may be added later if back_populates relationships exist.

