"""Re-export all Pydantic schemas."""
from .auth import Token, TokenData, UserCreate as AuthUserCreate, UserUpdate as AuthUserUpdate, UserResponse, UserLogin, PasswordReset
from .user import UserBase, UserCreate as UserCreateModel, UserUpdate as UserUpdateModel, UserResponse as UserResponseModel, UserInDB
from .analysis import SemanticAnalysisRequest, SemanticAnalysisResponse, PredictiveAnalysisRequest, PredictiveAnalysisResponse, AnalysisResult
from .visualization import VisualizationRequest, VisualizationResponse
from .document import Document, DocumentCreate, DocumentUpdate, DocumentInDB
from .validation import ValidationRequest, ValidationResponse, DefectResponse
from .traceability import TraceabilityEntry, TraceabilityNoteCreate, TraceabilityNoteResponse

# Create aliases to avoid conflicts
UserCreate = AuthUserCreate
UserUpdate = AuthUserUpdate

__all__ = [
    "Token",
    "TokenData",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserBase",
    "UserInDB",
    "UserLogin",
    "PasswordReset",
    "SemanticAnalysisRequest",
    "SemanticAnalysisResponse",
    "PredictiveAnalysisRequest",
    "PredictiveAnalysisResponse",
    "AnalysisResult",
    "VisualizationRequest",
    "VisualizationResponse",
    "Document",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentInDB",
    "ValidationRequest",
    "ValidationResponse",
    "DefectResponse",
    "TraceabilityEntry",
    "TraceabilityNoteCreate",
    "TraceabilityNoteResponse",
]
