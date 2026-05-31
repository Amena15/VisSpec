from pydantic import BaseModel
from typing import Optional


class SupervisorReviewDecision(BaseModel):
    decision: str  # "approved" | "changes_requested"
    comments: Optional[str] = None

