from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from models.user import User
from schemas.visualization import VisualizationRequest, VisualizationResponse
from services.visualization.visualizer import Visualizer
from utils.security import get_current_active_user
from config.database import get_db

router = APIRouter()

# Initialize visualization service
visualizer = Visualizer()

@router.post("/", response_model=VisualizationResponse)
def generate_visualization(
    request: VisualizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate visualization based on text input.
    Returns both Mermaid and PlantUML formats.
    """
    try:
        result = visualizer.generate_visualization(
            text=request.text,
            diagram_type=request.diagram_type,
            options=request.options,
        )

        return VisualizationResponse(
            id=str(uuid.uuid4()),
            diagram_type=request.diagram_type,
            mermaid_syntax=result["mermaid_syntax"],
            plantuml_syntax=result["plantuml_syntax"],
            title=result["title"],
            description=result["description"],
            actors=result.get("actors", []),
            use_cases=result.get("use_cases", []),
            relationships=result.get("relationships", []),
            generated_at=datetime.utcnow().isoformat()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid diagram type: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visualization generation failed: {str(e)}"
        )


@router.post("/usecase", response_model=VisualizationResponse)
def generate_usecase_diagram(
    request: VisualizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate UML Use Case diagram in both Mermaid and PlantUML formats."""
    try:
        result = visualizer.generate_usecase_diagram(request.text)

        return VisualizationResponse(
            id=str(uuid.uuid4()),
            diagram_type="usecase",
            mermaid_syntax=result["mermaid_syntax"],
            plantuml_syntax=result["plantuml_syntax"],
            title=result["title"],
            description=result["description"],
            actors=result.get("actors", []),
            use_cases=result.get("use_cases", []),
            relationships=result.get("relationships", []),
            generated_at=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Use case diagram generation failed: {str(e)}"
        )


@router.post("/sequence", response_model=VisualizationResponse)
def generate_sequence_diagram(
    request: VisualizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate UML Sequence diagram in both Mermaid and PlantUML formats."""
    try:
        result = visualizer.generate_sequence_diagram(request.text)

        return VisualizationResponse(
            id=str(uuid.uuid4()),
            diagram_type="sequence",
            mermaid_syntax=result["mermaid_syntax"],
            plantuml_syntax=result["plantuml_syntax"],
            title=result["title"],
            description=result["description"],
            actors=result.get("participants", []),
            use_cases=[m["message"] for m in result.get("messages", [])],
            relationships=[],
            generated_at=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sequence diagram generation failed: {str(e)}"
        )