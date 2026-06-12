"""
Processing status and hybrid architecture API routes.
Showcases the local/cloud processing capabilities.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from backend.models.user import User
from backend.utils.security import get_current_active_user
from backend.services.ai.hybrid_processor import hybrid_processor
from backend.core.logging import get_logger
from backend.core.task_queue import task_queue   # <-- ADD THIS

logger = get_logger(__name__)

# Remove prefix here (prefix is set in main.py)
router = APIRouter(tags=["processing"])


@router.get("/ping")
async def ping():
    return {"message": "pong from processing"}

@router.post("/test-task")
async def test_task(seconds: int = 3):
    async def long_task(s: int):
        import asyncio
        await asyncio.sleep(s)
        return f"Slept for {s} seconds"
    task_id = await task_queue.submit(long_task, seconds)
    return {"task_id": task_id}

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    result = task_queue.get_task(task_id)
    if not result:
        raise HTTPException(404, "Task not found")
    return result


@router.get("/status")
async def get_processing_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get the current status of hybrid processing components."""
    try:
        return hybrid_processor.get_processing_status()
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve processing status"
        )


@router.get("/architecture")
async def get_architecture_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get information about the hybrid processing architecture."""
    try:
        return {
            "architecture": "hybrid_local_cloud",
            "description": "Combines fast local processing with powerful cloud AI",
            "local_processing": {
                "components": ["PyMuPDF", "spaCy"],
                "capabilities": [
                    "Text extraction from PDF/DOCX/TXT",
                    "Tokenization and linguistic analysis",
                    "Basic actor identification",
                    "Modal verb detection",
                    "Vague term identification",
                    "Text cleaning and normalization"
                ],
                "benefits": [
                    "Fast processing (no network latency)",
                    "No API costs",
                    "Privacy (data stays local)",
                    "Reliable (always available)"
                ]
            },
            "cloud_processing": {
                "provider": "Groq API",
                "model": "LLaMA 3",
                "capabilities": [
                    "Semantic requirement extraction",
                    "Advanced defect detection",
                    "Complex categorization",
                    "Requirement organization",
                    "Complexity estimation",
                    "Professional prompt engineering"
                ],
                "benefits": [
                    "Advanced AI capabilities",
                    "Better accuracy",
                    "Contextual understanding",
                    "Professional-grade analysis"
                ]
            },
            "processing_flow": [
                "1. Document upload received",
                "2. Local text extraction (PyMuPDF)",
                "3. Local NLP preprocessing (spaCy)",
                "4. Cloud AI processing (Groq + LLaMA 3)",
                "5. Result integration and storage"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting architecture info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve architecture information"
        )