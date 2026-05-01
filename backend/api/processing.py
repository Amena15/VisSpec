"""
Processing status and hybrid architecture API routes.
Showcases the local/cloud processing capabilities.
"""
from fastapi import APIRouter, Depends
from models.user import User
from utils.security import get_current_active_user
from services.ai.hybrid_processor import hybrid_processor

router = APIRouter(prefix="/api/processing", tags=["processing"])

@router.get("/status")
def get_processing_status(current_user: User = Depends(get_current_active_user)):
    """
    Get the current status of hybrid processing components.
    Shows which local and cloud services are available.
    """
    return hybrid_processor.get_processing_status()

@router.get("/architecture")
def get_architecture_info(current_user: User = Depends(get_current_active_user)):
    """
    Get information about the hybrid processing architecture.
    Explains the local vs cloud processing split.
    """
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
