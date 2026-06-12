"""Re-export all SQLAlchemy models."""
from backend.models.user import User, UserRole
from backend.models.project import Project
from backend.models.document import RequirementDocument
from backend.models.requirement import Requirement
from backend.models.requirement_history import RequirementVersionHistory  # ADD THIS
from backend.models.validation import ValidationSession, Defect
from backend.models.diagram import Diagram, DiagramElement
from backend.models.metrics import ProjectMetrics
from backend.models.traceability import TraceabilityMatrix, TraceabilityNote
from backend.models.review import ReviewAudit
from backend.models.auxiliary import PasswordResetToken, SystemLog, AIPromptLog, ExportReport
from backend.models.notification import Notification


__all__ = [
    "User", "UserRole",
    "PasswordResetToken", "SystemLog",
    "Project", "RequirementDocument", "Requirement",
    "RequirementVersionHistory",  # ADD THIS
    "ValidationSession", "Defect", "AIPromptLog",
    "Diagram", "DiagramElement", "ProjectMetrics",
    "TraceabilityMatrix", "TraceabilityNote",
    "ReviewAudit", "ExportReport", "Notification",
]