"""
IEEE-Compliant Diagram Generation API.

Uses LLM-powered semantic extraction (LLaMA 3) with fallback to rule-based.
Enforces BR-11 (no hallucinated actors) and BR-12 (max 15 sequence steps).
Generates both Mermaid and PlantUML syntax.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import uuid
import requests

from backend.models.user import User
from backend.models.diagram import Diagram, DiagramElement
from backend.models.validation import ValidationSession
from backend.utils.security import get_current_active_user
from backend.config.database import get_db
from backend.core.logging import get_logger

# NEW IEEE-compliant services
from backend.services.diagram.semantic_extractor import DiagramSemanticExtractor
from backend.services.diagram.plantuml_generator import PlantUMLGenerator
from backend.services.diagram.mermaid_generator import MermaidGenerator

logger = get_logger(__name__)

router = APIRouter()

# Initialize services
extractor = DiagramSemanticExtractor()
plantuml_gen = PlantUMLGenerator()
mermaid_gen = MermaidGenerator()


# -----------------------------------------------------------------------------
# Request / Response Models
# -----------------------------------------------------------------------------

class DiagramGenerationRequest(BaseModel):
    document_id: str
    diagram_type: str  # 'usecase', 'sequence', 'activity'
    scenario: Optional[str] = None


class DiagramGenerationResponse(BaseModel):
    success: bool
    diagram_id: Optional[str] = None
    plantuml_syntax: Optional[str] = None
    mermaid_syntax: Optional[str] = None
    mapping_data: Optional[dict] = None
    compliance: Optional[dict] = None
    generation_time_ms: Optional[int] = None
    total_elements: Optional[int] = None
    error: Optional[str] = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

async def _fetch_validated_requirements(db: AsyncSession, document_id: str) -> List[Dict[str, Any]]:
    """Fetch validated requirements for a document."""
    query = text("""
        SELECT req_id, doc_id, project_id, original_text, current_text,
               actors_json, modal_verbs_json, category, semantic_id,
               module_name, sequence_order, validation_status
        FROM requirements
        WHERE doc_id = :doc_id
          AND validation_status IN ('validated', 'passed')
        ORDER BY sequence_order, created_at
    """)
    result = await db.execute(query, {"doc_id": document_id})
    rows = result.fetchall()
    if not rows:
        return []
    return [
        {
            "req_id": r[0],
            "doc_id": r[1],
            "project_id": r[2],
            "original_text": r[3],
            "current_text": r[4],
            "actors_json": r[5],
            "modal_verbs_json": r[6],
            "category": r[7],
            "semantic_id": r[8],
            "module_name": r[9],
            "sequence_order": r[10],
            "validation_status": r[11]
        }
        for r in rows
    ]


def _combine_texts(requirements: List[Dict[str, Any]]) -> str:
    """Combine all requirement texts into one string."""
    texts = []
    for req in requirements:
        text = req.get("current_text") or req.get("original_text", "")
        if text:
            texts.append(text)
    return " ".join(texts)


def _extract_title(text: str) -> str:
    """Extract system title from text."""
    patterns = [
        r'(?:the|an|a)\s+(\w+\s+(?:\w+\s+)?system)',
        r'(\w+\s+system)',
        r'(\w+\s+application)',
        r'(\w+\s+platform)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()
    return "System"


# Common stop words ignored when grounding an extracted element against the
# source requirement text.
_GROUNDING_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "by",
    "is", "are", "be", "shall", "must", "will", "should", "may", "can", "system",
    "user", "data", "manage", "process", "perform", "view", "add", "delete",
    "update", "create", "handle", "use", "case",
}


def _significant_tokens(name: str) -> set:
    """Return lowercased alphanumeric tokens with stop words removed."""
    tokens = re.findall(r"[a-z0-9]+", (name or "").lower())
    return {t for t in tokens if len(t) > 2 and t not in _GROUNDING_STOPWORDS}


def _is_grounded(name: str, source_token_index: set) -> bool:
    """
    A diagram element is grounded (traceable) if at least one of its significant
    tokens appears in the combined source requirement text. Elements whose every
    significant token is absent from the requirements are treated as hallucinations
    (invented by the LLM with no grounding requirement).
    """
    tokens = _significant_tokens(name)
    if not tokens:
        # No discriminating tokens (e.g. "Manage System") -> accept, not a hallucination.
        return True
    return bool(tokens & source_token_index)


def _enforce_traceability(
    data: Dict[str, Any],
    requirements: List[Dict[str, Any]],
    diagram_type: str,
) -> Dict[str, Any]:
    """
    Stage 5 — Traceability Enforcement for the LLM-extraction diagram path.

    The LLM extractor does not attach a source_req_id to each element, so we
    verify traceability against the *parsed requirement list* instead: an actor or
    use case is kept only if it is grounded in the combined source requirement text.
    Any element that is not grounded is counted as a rejected hallucination and
    dropped from the diagram so it can never reach the rendered syntax.

    Returns a dict with the (possibly mutated) `data`, the number of rejected
    elements, and the list of rejected element labels.
    """
    combined_text = " ".join(
        (req.get("current_text") or req.get("original_text", "")) for req in requirements
    )
    source_token_index = set(re.findall(r"[a-z0-9]+", combined_text.lower()))

    rejected = 0
    rejected_labels: List[str] = []

    if diagram_type == "usecase":
        kept_uc = []
        for uc in data.get("use_cases", []):
            name = uc.get("name") if isinstance(uc, dict) else str(uc)
            if _is_grounded(name, source_token_index):
                kept_uc.append(uc)
            else:
                rejected += 1
                rejected_labels.append(f"use_case:{name}")
        data["use_cases"] = kept_uc

        kept_actors = []
        for actor in data.get("actors", []):
            name = actor.get("name") if isinstance(actor, dict) else str(actor)
            if _is_grounded(name, source_token_index):
                kept_actors.append(actor)
            else:
                rejected += 1
                rejected_labels.append(f"actor:{name}")
        data["actors"] = kept_actors

        # Prune associations referencing dropped nodes.
        kept_uc_names = {
            (u.get("name") if isinstance(u, dict) else str(u)) for u in kept_uc
        }
        kept_actor_names = {
            (a.get("name") if isinstance(a, dict) else str(a)) for a in kept_actors
        }
        data["associations"] = [
            a for a in data.get("associations", [])
            if (a.get("use_case") in kept_uc_names and a.get("actor") in kept_actor_names)
        ]

    elif diagram_type == "activity":
        kept = []
        for act in data.get("activities", []):
            name = act.get("name") if isinstance(act, dict) else str(act)
            if _is_grounded(name, source_token_index):
                kept.append(act)
            else:
                rejected += 1
                rejected_labels.append(f"activity:{name}")
        data["activities"] = kept

    elif diagram_type == "sequence":
        # Sequence messages: ground on the free-text message body.
        kept = []
        for msg in data.get("messages", []):
            name = msg.get("message") if isinstance(msg, dict) else str(msg)
            if _is_grounded(name, source_token_index):
                kept.append(msg)
            else:
                rejected += 1
                rejected_labels.append(f"message:{str(name)[:40]}")
        data["messages"] = kept

    return {
        "data": data,
        "hallucination_rejected_count": rejected,
        "rejected_elements": rejected_labels,
    }



# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post("/generate", response_model=DiagramGenerationResponse)
async def generate_ieee_compliant_diagram(
    request: DiagramGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate IEEE-compliant diagram using LLM-powered extraction.
    Enforces BR-11 (no hallucinated actors) and BR-12 (max 15 sequence steps).
    """
    try:
        # 1. Fetch requirements
        requirements = await _fetch_validated_requirements(db, request.document_id)
        if not requirements:
            return DiagramGenerationResponse(
                success=False,
                error="No validated requirements found for this document"
            )

        combined_text = _combine_texts(requirements)
        if not combined_text:
            return DiagramGenerationResponse(
                success=False,
                error="No requirement text found"
            )

        # 2. Get project_id from first requirement
        project_id = requirements[0].get("project_id")
        if not project_id:
            return DiagramGenerationResponse(
                success=False,
                error="Could not determine project_id from requirements"
            )

        # 3. Extract semantic data using LLM (with fallback)
        try:
            if request.diagram_type == "usecase":
                data = await extractor.extract_usecase_data(combined_text)
            elif request.diagram_type == "sequence":
                data = await extractor.extract_sequence_data(combined_text, request.scenario)
            elif request.diagram_type == "activity":
                data = await extractor.extract_activity_data(combined_text)
            else:
                return DiagramGenerationResponse(
                    success=False,
                    error=f"Unsupported diagram type: {request.diagram_type}"
                )
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Use fallback
            data = extractor._fallback_extract(combined_text)
            if request.diagram_type == "sequence":
                # Ensure sequence data has required fields
                data.setdefault("participants", ["User", "System"])
                data.setdefault("messages", [
                    {"from": "User", "to": "System", "message": "Perform action"},
                    {"from": "System", "to": "User", "message": "Return result"}
                ])

        # 3b. Stage 5 — Traceability Enforcement (real BR-11 check).
        # Drop any actor / use case / message the LLM invented that is not grounded
        # in the parsed requirement list, and count how many were rejected.
        traceability = _enforce_traceability(data, requirements, request.diagram_type)
        data = traceability["data"]
        hallucination_rejected_count = traceability["hallucination_rejected_count"]
        rejected_elements = traceability["rejected_elements"]
        if hallucination_rejected_count:
            logger.info(
                f"BR-11 traceability: rejected {hallucination_rejected_count} "
                f"untraceable element(s): {rejected_elements}"
            )

        # 4. Generate PlantUML and Mermaid (only from verified, grounded nodes)
        if request.diagram_type == "usecase":
            plantuml_syntax = plantuml_gen.generate_usecase_plantuml(data)
            mermaid_syntax = mermaid_gen.generate_usecase_mermaid(data)
            total_elements = len(data.get("actors", [])) + len(data.get("use_cases", []))
        elif request.diagram_type == "sequence":
            plantuml_syntax = plantuml_gen.generate_sequence_plantuml(data)
            mermaid_syntax = mermaid_gen.generate_sequence_mermaid(data)
            total_elements = len(data.get("messages", []))
            # BR-12 compliance
            data["truncated"] = len(data.get("messages", [])) >= 15
        elif request.diagram_type == "activity":
            plantuml_syntax = plantuml_gen.generate_activity_plantuml(data)
            mermaid_syntax = mermaid_gen.generate_activity_mermaid(data)
            total_elements = len(data.get("activities", [])) + len(data.get("decisions", []))

        # 5. Store diagram in database
        try:
            # Handle validation_id
            potential_validation_id = f"{request.document_id}_validation"
            val_stmt = select(ValidationSession).where(
                ValidationSession.validation_id == potential_validation_id
            )
            val_result = await db.execute(val_stmt)
            validation_id = potential_validation_id if val_result.scalar_one_or_none() else None

            diagram = Diagram(
                project_id=project_id,
                validation_id=validation_id,
                diagram_type=request.diagram_type,
                scenario_name=request.scenario,
                mermaid_syntax=mermaid_syntax,
                plantuml_syntax=plantuml_syntax,
                syntax_valid=1,
                total_elements=total_elements,
                hallucination_rejected_count=hallucination_rejected_count,
                generation_time_ms=None
            )
            db.add(diagram)
            await db.flush()

            # Store diagram elements (optional)
            # ... can be added later

            await db.commit()
            diagram_id = diagram.diagram_id
        except Exception as e:
            logger.warning(f"Failed to store diagram in database: {e}")
            diagram_id = None

        # 6. Build compliance response
        compliance = {
            "br_11_compliant": hallucination_rejected_count == 0,  # 0 untraceable nodes kept out
            "br_12_compliant": not data.get("truncated", False),
            "hallucination_rejected_count": hallucination_rejected_count,
            "rejected_elements": rejected_elements,
            "warning": data.get("warning") if data.get("truncated") else None
        }

        return DiagramGenerationResponse(
            success=True,
            diagram_id=diagram_id,
            plantuml_syntax=plantuml_syntax,
            mermaid_syntax=mermaid_syntax,
            mapping_data=data,
            compliance=compliance,
            generation_time_ms=None,
            total_elements=total_elements
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Diagram generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diagram generation failed: {str(e)}"
        )


@router.get("/project/{project_id}/diagrams")
async def get_project_diagrams(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all diagrams for a project."""
    try:
        stmt = select(Diagram).where(Diagram.project_id == project_id)
        result = await db.execute(stmt)
        diagrams = result.scalars().all()
        return {
            "diagrams": [
                {
                    "diagram_id": d.diagram_id,
                    "diagram_type": d.diagram_type,
                    "scenario_name": d.scenario_name,
                    "mermaid_syntax": d.mermaid_syntax,
                    "plantuml_syntax": d.plantuml_syntax,
                    "syntax_valid": d.syntax_valid,
                    "total_elements": d.total_elements,
                    "created_at": d.created_at
                }
                for d in diagrams
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagram/{diagram_id}")
async def get_diagram_details(
    diagram_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed diagram information with traceability."""
    try:
        stmt = select(Diagram).where(Diagram.diagram_id == diagram_id)
        result = await db.execute(stmt)
        diagram = result.scalar_one_or_none()
        if not diagram:
            raise HTTPException(status_code=404, detail="Diagram not found")

        return {
            "diagram": {
                "diagram_id": diagram.diagram_id,
                "project_id": diagram.project_id,
                "validation_id": diagram.validation_id,
                "diagram_type": diagram.diagram_type,
                "scenario_name": diagram.scenario_name,
                "mermaid_syntax": diagram.mermaid_syntax,
                "plantuml_syntax": diagram.plantuml_syntax,
                "syntax_valid": diagram.syntax_valid,
                "total_elements": diagram.total_elements,
                "created_at": diagram.created_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/render-plantuml-svg")
async def render_plantuml_to_svg(
    plantuml_encoded: str = Body(..., media_type="text/plain"),
    current_user: User = Depends(get_current_active_user)
):
    """Render PlantUML syntax to SVG through backend to bypass browser CORS."""
    try:
        encoded = (plantuml_encoded or "").strip()
        if not encoded:
            raise HTTPException(status_code=400, detail="Missing PlantUML encoded content")

        endpoints = [
            f"https://www.planttext.com/api/plantuml/svg/{encoded}",
            f"https://www.plantuml.com/plantuml/svg/{encoded}",
        ]

        last_error = None
        for url in endpoints:
            try:
                upstream = requests.get(url, timeout=30)
                if upstream.status_code == 200 and upstream.text:
                    return Response(
                        content=upstream.text,
                        media_type="image/svg+xml",
                        headers={"Content-Disposition": "attachment; filename=diagram.svg"},
                    )
                last_error = f"status={upstream.status_code}"
            except Exception as ex:
                last_error = str(ex)

        raise HTTPException(status_code=502, detail=f"Failed to render SVG: {last_error}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("SVG rendering failed")
        raise HTTPException(status_code=500, detail=f"SVG rendering failed: {str(e)}")