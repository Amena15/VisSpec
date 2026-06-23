"""Document upload and management API routes.

Implements REQ_04 (Document Upload), REQ_05 (Text Extraction & Parsing),
REQ_06 (Structure Identification), and REQ_07 (Project Data Management).
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import Any, Dict, List, Optional

from backend.models.user import User
from backend.models.project import Project
from backend.models.document import RequirementDocument
from backend.models.requirement import Requirement
from backend.schemas.document import (
    DocumentUploadResponse,
    DocumentSummary,
    DocumentDetail,
    DocumentDeleteResponse,
)
from backend.services.document.parser import DocumentParser
from backend.utils.security import get_current_active_user
from backend.config.database import get_db
from backend.core.config import settings
from backend.core.logging import get_logger

# Import TextCleaner with fallback
try:
    from backend.services.ai.text_cleaner import TextCleaner
except ImportError:
    TextCleaner = None

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_json_loads(value: Optional[str], default=None):
    """Safely load JSON string, returning default on failure."""
    if not value:
        return default if default is not None else []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


def _count_meaningful_words(text: str) -> int:
    """Count words with at least 2 alphabetic characters."""
    words = text.split()
    return sum(1 for word in words if sum(1 for ch in word if ch.isalpha()) >= 2)


def _assess_extraction_quality(
    *,
    file_extension: str,
    extracted_text: str,
    word_count: int,
    page_count: Optional[int],
    parser_scanned_flag: int,
) -> Dict[str, Any]:
    """Assess extraction quality and decide whether to reject obviously unreadable uploads."""
    text = extracted_text or ""
    stripped = text.strip()
    effective_pages = max(int(page_count or 1), 1)

    meaningful_word_count = _count_meaningful_words(text)
    words_per_page = word_count / effective_pages if effective_pages else word_count
    meaningful_ratio = (meaningful_word_count / word_count) if word_count > 0 else 0.0

    warnings: List[str] = []
    confidence = "high"
    reject_upload = False

    is_pdf = file_extension == "pdf"
    is_scanned_suspected = bool(parser_scanned_flag)

    # Reject only when extraction is clearly unusable.
    if len(stripped) == 0 or word_count == 0:
        reject_upload = True
        confidence = "high"
        warnings.append("No readable text extracted from document.")
    elif is_pdf and (parser_scanned_flag == 1 and words_per_page < 8):
        reject_upload = True
        confidence = "high"
        warnings.append("PDF appears scanned and extracted text is insufficient for analysis.")
    elif is_pdf and words_per_page < 10:
        is_scanned_suspected = True
        confidence = "medium"
        warnings.append("Very low text density detected for PDF; extraction quality may be poor.")

    # Non-fatal quality warnings to make quality visible to users.
    if word_count > 0 and meaningful_ratio < 0.55:
        warnings.append("Extracted text appears noisy (low meaningful word ratio).")
        if confidence == "high":
            confidence = "medium"

    if word_count > 0 and len(stripped) < max(40, int(word_count * 2.5)):
        warnings.append("Extracted text may be truncated or overly compressed.")
        if confidence == "high":
            confidence = "medium"

    quality_score = 100.0
    if word_count == 0:
        quality_score = 0.0
    else:
        density_score = min(words_per_page / 40.0, 1.0) * 40.0
        meaning_score = meaningful_ratio * 50.0
        length_score = min(len(stripped) / 300.0, 1.0) * 10.0
        quality_score = round(max(0.0, min(100.0, density_score + meaning_score + length_score)), 1)

    return {
        "reject_upload": reject_upload,
        "is_scanned_pdf": 1 if is_scanned_suspected else 0,
        "warnings": warnings,
        "quality_score": quality_score,
        "confidence": confidence,
        "meaningful_word_count": meaningful_word_count,
        "words_per_page": round(words_per_page, 2),
        "meaningful_ratio": round(meaningful_ratio, 3),
    }


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a requirement document (PDF, DOCX, or TXT).

    Implements UC_04:
    - Validates file type (BR-07: only .pdf and .docx accepted, plus .txt)
    - Validates file size (BR-08: max 10MB)
    - Detects scanned/image-based PDFs
    - Extracts text, structure, and requirements
    - Returns Document Summary (word count, # requirements found)
    """
    # ------------------------------------------------------------------
    # 1. Validate file type (BR-07)
    # ------------------------------------------------------------------
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed_extensions = {"pdf", "docx", "txt"}

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: .{ext}. Only PDF, DOCX, and TXT files are accepted. Please convert your document to one of these formats.",
        )

    # ------------------------------------------------------------------
    # 2. Validate file size (BR-08: max 10MB)
    # ------------------------------------------------------------------
    file_content = await file.read()
    file_size = len(file_content)
    max_size = 10 * 1024 * 1024  # 10MB

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({file_size / (1024 * 1024):.1f}MB). Maximum size is {max_size // (1024 * 1024)}MB. Please split your document into smaller files or compress it.",
        )

    # ------------------------------------------------------------------
    # 3. Check user storage quota (NFR_SP1)
    # ------------------------------------------------------------------
    new_usage = current_user.storage_used_bytes + file_size
    quota_bytes = current_user.storage_quota_mb * 1024 * 1024
    
    if new_usage > quota_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Storage quota exceeded. Your quota: {current_user.storage_quota_mb}MB, Currently used: {current_user.storage_used_bytes / (1024 * 1024):.1f}MB, This file: {file_size / (1024 * 1024):.1f}MB. Please delete old documents or upgrade your plan.",
        )

    # ------------------------------------------------------------------
    # 4. Parse document
    # ------------------------------------------------------------------
    try:
        from services.document.parser import DocumentParser
        parser = DocumentParser()
        parse_result = parser.parse(file_content, filename)
        
        if "error" in parse_result:
            error_msg = parse_result["error"]
            if "not a zip file" in error_msg or "File is not a zip file" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid DOCX file. The file appears to be corrupted or not a valid DOCX document."
                )
            elif "PyMuPDF not installed" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="PDF processing library not available. Please contact support or try uploading as DOCX or TXT format."
                )
            elif "python-docx not installed" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="DOCX processing library not available. Please contact support or try uploading as PDF or TXT format."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Document parsing failed: {error_msg}. Please ensure the file is not corrupted and try again."
                )
        
        extracted_text = parse_result.get("text", "")
        word_count = parse_result.get("word_count", 0)
        page_count = parse_result.get("page_count", 0)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing document: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document processing failed. Please try uploading the file again or contact support if the issue persists."
        )
    
    # ------------------------------------------------------------------
    # 5. Assess extraction quality and scanned-PDF risk
    # ------------------------------------------------------------------
    extraction_quality = _assess_extraction_quality(
        file_extension=ext,
        extracted_text=extracted_text,
        word_count=word_count,
        page_count=page_count,
        parser_scanned_flag=parse_result.get("is_scanned_pdf", 0),
    )
    is_scanned_pdf = extraction_quality["is_scanned_pdf"]
    quality_warnings = list(extraction_quality["warnings"])

    if extraction_quality["reject_upload"]:
        logger.warning(
            "Rejecting upload due to low extraction quality",
            extra={
                "filename": filename,
                "file_extension": ext,
                "word_count": word_count,
                "page_count": page_count,
                "quality_score": extraction_quality["quality_score"],
                "quality_confidence": extraction_quality["confidence"],
                "warnings": quality_warnings,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No usable readable text detected. Please upload a searchable PDF with a text layer or a clearer source document.",
        )
    
    # Generate document ID early for logging purposes
    doc_id = str(uuid.uuid4())
    
    # Extract requirements using enhanced parser for better quality and speed
    logger.info(f"Extracting requirements from document {filename}", extra={"doc_id": doc_id, "doc_filename": filename})
    
    try:
        requirements = parser.extract_requirements(extracted_text)
        requirements_count = len(requirements)
        
        # Add warning if no requirements found
        if requirements_count == 0:
            extraction_warning = (
                "No clear requirements were extracted. Document may lack explicit modal verbs "
                "(shall, must, should, will, may) or extraction quality is low."
            )
            quality_warnings.append(extraction_warning)
            logger.warning(
                f"No clear requirements found in document {filename}. "
                f"Document may not contain modal verbs (shall, must, should, will, may). "
                f"Word count: {word_count}",
                extra={"doc_id": doc_id, "doc_filename": filename, "word_count": word_count}
            )

        # Quality validation: suspiciously low requirement yield for longer documents.
        if word_count >= 120 and requirements_count <= 1:
            low_yield_warning = (
                "Extraction quality warning: very few requirements detected for a long document. "
                "Please review extracted requirements before analysis."
            )
            quality_warnings.append(low_yield_warning)
            logger.warning(
                "Low requirement extraction yield detected",
                extra={
                    "doc_id": doc_id,
                    "doc_filename": filename,
                    "word_count": word_count,
                    "requirements_count": requirements_count,
                    "quality_score": extraction_quality["quality_score"],
                },
            )
        
        logger.info(f"Successfully extracted {requirements_count} requirements", extra={"doc_id": doc_id, "req_count": requirements_count})
        
    except Exception as e:
        logger.error(f"Error extracting requirements: {e}", extra={"doc_id": doc_id, "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract requirements: {str(e)}"
        )
    
    # Apply text cleaning only if needed (optimized for speed)
    if TextCleaner and requirements_count > 0:
        try:
            logger.info(f"Applying text cleaning to {len(requirements)} requirements", extra={"doc_id": doc_id, "req_count": len(requirements)})
            
            # Clean requirements batch
            cleaned_requirements = TextCleaner.clean_requirements_batch(requirements)
            requirements = cleaned_requirements
            
            # Also clean the main document text (idempotent if already cleaned)
            cleaned_extracted_text = TextCleaner.clean_requirement_text(extracted_text)
            
            # Log cleaning results
            if cleaned_extracted_text != extracted_text:
                logger.info("Document text was cleaned during upload")
                logger.debug(f"Original length: {len(extracted_text)}, Cleaned length: {len(cleaned_extracted_text)}")
            
            extracted_text = cleaned_extracted_text
            
            logger.info(f"Text cleaning completed successfully for {len(requirements)} requirements", extra={"doc_id": doc_id, "req_count": len(requirements)})
        
        except Exception as e:
            logger.error(
                "Text cleaning failed during upload",
                extra={"doc_id": doc_id, "doc_filename": filename, "error": str(e)},
            )
            # Continue with original requirements if cleaning fails
            warning_msg = "Text cleaning failed; proceeding with original extracted text."
            quality_warnings.append(warning_msg)
            logger.warning(
                warning_msg,
                extra={"doc_id": doc_id, "doc_filename": filename},
            )
    
    # Identify logical sections
    sections = parser.identify_structure(extracted_text)
    sections_count = len(sections)
    sections_titles = [section["title"] for section in sections]
    
    # Sanitize text for full-text search
    sanitized_text = parser.sanitize_text(extracted_text)
    
    # Create document record
    document = RequirementDocument(
        doc_id=doc_id,
        project_id=project_id,
        filename=filename,
        file_extension=ext,
        file_size_bytes=file_size,
        word_count=word_count,
        page_count=parse_result.get("page_count"),
        status="Ready for Analysis",
        content=file_content,  # Store original binary file
        extracted_text=sanitized_text,  # Store extracted text for analysis
        upload_date=datetime.now(timezone.utc),
        uploaded_by=current_user.user_id,
        is_scanned_pdf=is_scanned_pdf,
        parse_error=" | ".join(dict.fromkeys(quality_warnings)) if quality_warnings else None,
        extracted_author=parse_result.get("extracted_author"),
        extracted_version=parse_result.get("extracted_version"),
    )
    
    # Save document to database
    db.add(document)
    await db.commit()
    
    # Update user storage usage
    current_user.storage_used_bytes = new_usage
    await db.commit()
    
    # Save requirements to database
    for i, req in enumerate(requirements):
        # Sanitize individual requirement text
        original_text = req.get("original_text", "")
        sanitized_text = parser.sanitize_text(original_text)
        
        requirement = Requirement(
            req_id=str(uuid.uuid4()),
            doc_id=doc_id,
            project_id=project_id,
            req_identifier=req.get("req_identifier", f"REQ-{i+1:03d}"),
            original_text=sanitized_text,
            current_text=sanitized_text,
            word_count=req.get("word_count", 0),
            sequence_order=req.get("sequence_order", i),
            section_header=req.get("section_header", ""),
        )
        db.add(requirement)
    
    await db.commit()
    
    # Auto-organize requirements for new document (professional flow)
    try:
        logger.info("Auto-organizing requirements for new document", extra={"doc_id": doc_id})
        result = await db.execute(select(Requirement).where(Requirement.doc_id == doc_id))
        req_objects = result.scalars().all()
        raw_reqs = []
        for r in req_objects:
            raw_reqs.append({
                "req_id": r.req_id,
                "req_identifier": r.req_identifier,
                "section_header": r.section_header,
                "original_text": r.original_text,
                "current_text": r.current_text,
                "word_count": r.word_count,
                "sequence_order": r.sequence_order,
            })
        from services.ai.requirement_organizer import requirement_organizer
        
        # Use global TextCleaner import
        if TextCleaner:
            cleaned_reqs = TextCleaner.clean_requirements_batch(raw_reqs)
        else:
            cleaned_reqs = raw_reqs  # Fallback if TextCleaner not available
        full_text = extracted_text
        # Use LLM for enrichment when API key is present, otherwise rule-based
        use_llm = bool(settings.GROQ_API_KEY)
        logger.info(f"Using {'LLM-based' if use_llm else 'rule-based'} auto-enrichment")
        enriched_reqs = requirement_organizer.organize_and_enrich(cleaned_reqs, full_text, use_llm=use_llm)
        
        # Update DB requirements
        updated = 0
        for enriched, r in zip(enriched_reqs, req_objects):
            r.semantic_id = enriched.get('semantic_id')
            r.module_name = enriched.get('module_name', 'General')
            r.category = enriched.get('category', 'functional')
            r.category_confidence = enriched.get('category_confidence', 0.8)
            # JSON fields
            actors = enriched.get('actors', [])
            r.actors_json = json.dumps(actors)
            r.modal_verbs_json = json.dumps(enriched.get('modal_verbs', []))
            r.vague_terms_json = json.dumps(enriched.get('vague_terms', []))
            updated += 1
        await db.commit()
        logger.info(f"Auto-organized {updated} requirements", extra={"doc_id": doc_id, "updated_count": updated})
    except Exception as e:
        logger.warning(f"Auto-organize failed: {e} - manual fix available", extra={"doc_id": doc_id, "error": str(e)})
    
    # Update project status to 'ready' after successful document processing
    try:
        result = await db.execute(select(Project).where(Project.project_id == project_id))
        project = result.scalar_one_or_none()
        if project:
            project.status = "ready"
            project.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            await db.commit()
            logger.info(f"Updated project {project_id} status to 'ready' after document processing", extra={"project_id": project_id, "doc_id": doc_id})
    except Exception as e:
        logger.warning(f"Failed to update project status: {e}", extra={"project_id": project_id, "doc_id": doc_id, "error": str(e)})
    
    return DocumentUploadResponse(
        doc_id=doc_id,
        project_id=project_id,
        filename=filename,
        file_extension=ext,
        file_size_bytes=file_size,
        word_count=word_count,
        page_count=parse_result.get("page_count"),
        status="Analyzed & Organized",
        requirements_found=requirements_count,
        sections_found=sections_titles,
        extracted_text=extracted_text,
        upload_date=datetime.now(timezone.utc),
        extraction_quality_score=extraction_quality["quality_score"],
        extraction_warnings=list(dict.fromkeys(quality_warnings)),
    )


@router.get("/", response_model=List[DocumentSummary])
async def list_documents(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the authenticated user, optionally filtered by project."""
    try:
        # Eager load requirements and validation_sessions to prevent async lazy-loading errors
        result = await db.execute(
            select(RequirementDocument)
            .filter(RequirementDocument.uploaded_by == current_user.user_id)
            .options(
                selectinload(RequirementDocument.requirements),
                selectinload(RequirementDocument.validation_sessions)
            )
            .order_by(RequirementDocument.upload_date.desc())
        )
        docs = result.scalars().all()

        result = []
        for d in docs:
            # Get requirements count safely
            try:
                req_count = len(d.requirements) if d.requirements else 0
            except:
                req_count = 0

            # Calculate quality score and defect count from validation sessions
            quality_score = 0
            defect_count = 0
            
            try:
                # Get defect count from validation sessions (more accurate)
                if d.validation_sessions:
                    # Use the most recent validation session
                    latest_validation = max(d.validation_sessions, key=lambda v: v.validation_date if v.validation_date else "")
                    defect_count = latest_validation.defect_count or 0
                    quality_score = latest_validation.overall_score or 50
                    
                    # Data consistency check: defects should not exist without requirements
                    if defect_count > 0 and req_count == 0:
                        logger.warning(
                            f"Data inconsistency detected for document {d.doc_id}: "
                            f"{defect_count} defects but {req_count} requirements. "
                            f"Setting defect_count to 0 for consistency.",
                            extra={"doc_id": d.doc_id, "defect_count": defect_count, "req_count": req_count}
                        )
                        defect_count = 0
                        quality_score = 100.0
                        
                        # Fix the validation session in database to prevent future occurrences
                        try:
                            latest_validation.defect_count = 0
                            latest_validation.overall_score = 100.0
                            await db.commit()
                            logger.info(f"Fixed validation session {latest_validation.validation_id} for document {d.doc_id}")
                        except Exception as fix_error:
                            logger.error(f"Failed to fix validation session: {fix_error}")
                            await db.rollback()
                else:
                    # Fallback: calculate from requirements if no validation sessions exist
                    if d.requirements:
                        valid_requirements = 0
                        total_requirements = len(d.requirements)
                        
                        for req in d.requirements:
                            if req.validation_status == 'approved':
                                valid_requirements += 1
                        
                        # Quality score: percentage of approved requirements + word count factor
                        if total_requirements > 0:
                            approval_rate = (valid_requirements / total_requirements) * 100
                            word_count_bonus = min(10, (d.word_count or 0) / 1000 * 5)
                            quality_score = min(100, approval_rate + word_count_bonus)
                        else:
                            quality_score = 50
                    else:
                        quality_score = 50  # Default score for documents with no requirements
                        defect_count = 0
            except Exception as e:
                print(f"Error calculating quality score for document {d.doc_id}: {e}")
                quality_score = 50
                defect_count = 0

            result.append(
                DocumentSummary(
                    doc_id=d.doc_id,
                    project_id=d.project_id,
                    filename=d.filename,
                    file_extension=d.file_extension,
                    file_size_bytes=d.file_size_bytes,
                    word_count=d.word_count or 0,
                    extracted_text=d.extracted_text,
                    page_count=d.page_count,
                    status=d.status,
                    requirements_found=req_count,
                    upload_date=d.upload_date,
                    quality_score=round(quality_score, 1),
                    defect_count=defect_count,
                )
            )
        return result
    except Exception as e:
        print(f"Error in documents API: {e}")
        # Return empty list as fallback
        return []


@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single document with its extracted requirements."""
    try:
        # Simplified query to avoid SQLAlchemy errors
        result = await db.execute(
            select(RequirementDocument).filter(RequirementDocument.doc_id == doc_id)
        )
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
        if doc.uploaded_by != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
        from backend.services.document.parser import DocumentParser
        parser = DocumentParser()
        structure_source = (doc.extracted_text or "") if isinstance(doc.extracted_text, str) else ""
        try:
            sections_data = parser.identify_structure(structure_source)
        except Exception as parse_err:
            logger.warning("identify_structure failed for doc %s: %s", doc_id, parse_err, extra={"doc_id": doc_id})
            sections_data = []
        
        # Get requirements
        req_result = await db.execute(
            select(Requirement).filter(Requirement.doc_id == doc_id).order_by(Requirement.sequence_order)
        )
        requirements = req_result.scalars().all()

        print(f"DEBUG: Found {len(requirements)} requirements for document {doc_id}")

        req_list = []
        import json
        for req in requirements:
            actors, modal_verbs, vague_terms = [], [], []
            try:
                if req.actors_json: actors = json.loads(req.actors_json)
                if req.modal_verbs_json: modal_verbs = json.loads(req.modal_verbs_json)
                if req.vague_terms_json: vague_terms = json.loads(req.vague_terms_json)
            except json.JSONDecodeError:
                pass

            # FOOLPROOF DATE HANDLING: Check if it's a datetime object before calling isoformat
            req_date = req.created_at.isoformat() if hasattr(req.created_at, 'isoformat') else str(req.created_at) if req.created_at else ""

            req_list.append({
                "req_id": req.req_id,
                "req_identifier": str(req.req_identifier) if req.req_identifier else "",
                "original_text": str(req.original_text) if req.original_text else "",
                "current_text": str(req.current_text) if req.current_text else "",
                "word_count": req.word_count or 0,
                "sequence_order": req.sequence_order or 0,
                "category": req.category,
                "module_name": req.module_name,
                "semantic_id": req.semantic_id,
                "category_confidence": req.category_confidence,
                "actors": actors,
                "modal_verbs": modal_verbs,
                "vague_terms": vague_terms,
                "validation_status": req.validation_status,
                "upload_date": req_date,
            })
        
        # FOOLPROOF DATE HANDLING for the document upload date
        doc_date = doc.upload_date.isoformat() if hasattr(doc.upload_date, 'isoformat') else str(doc.upload_date) if doc.upload_date else ""

        response_data = {
            "doc_id": doc_id,
            "project_id": doc.project_id,
            "filename": doc.filename,
            "file_extension": doc.file_extension,
            "file_size_bytes": doc.file_size_bytes,
            "word_count": doc.word_count or 0,
            "page_count": doc.page_count,
            "status": doc.status,
            "content": str(doc.content) if doc.content else "",
            "extracted_text": str(doc.extracted_text) if doc.extracted_text else "",
            "upload_date": doc_date,
            "uploaded_by": doc.uploaded_by,
            "is_scanned_pdf": doc.is_scanned_pdf,
            "extracted_author": doc.extracted_author,
            "extracted_version": doc.extracted_version,
            "sections": sections_data,
            "sections_found": [str(s.get("title", "")) for s in sections_data],
            "requirements": req_list,
        }
        
        try:
            return Response(
                content=json.dumps(response_data),
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "Content-Type": "application/json",
                }
            )
        except (TypeError, ValueError) as json_error:
            print(f"JSON serialization error: {json_error}")
            raise
            
    except Exception as e:
        print(f"Error in get_document: {e}")
        return {
            "doc_id": doc_id,
            "project_id": "",
            "filename": "Document",
            "file_extension": "txt",
            "file_size_bytes": 0,
            "word_count": 0,
            "page_count": 0,
            "status": "Ready for Analysis",
            "extracted_text": "",
            "upload_date": "",
            "requirements": [],
        }

@router.post("/enrich-document/{doc_id}")
async def enrich_document_endpoint(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Manually trigger enrichment for existing document"""
    try:
        # Get document
        result = await db.execute(
            select(RequirementDocument).filter(RequirementDocument.doc_id == doc_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(404, "Document not found")
        
        # Get requirements
        result = await db.execute(
            select(Requirement).filter(Requirement.doc_id == doc_id)
        )
        requirements = result.scalars().all()
        
        if not requirements:
            return {"message": "No requirements found to enrich"}
        
        # Apply enrichment
        from services.ai.requirement_organizer import requirement_organizer
        
        # Create requirement objects for enrichment
        req_objects = []
        for req in requirements:
            req_objects.append({
                "req_id": req.req_id,
                "req_identifier": req.req_identifier,
                "section_header": req.section_header,
                "original_text": req.original_text,
                "current_text": req.current_text,
                "word_count": req.word_count,
                "sequence_order": req.sequence_order,
            })
        
        # Use global TextCleaner import
        if TextCleaner:
            cleaned_requirements = TextCleaner.clean_requirements_batch(req_objects)
        else:
            cleaned_requirements = req_objects  # Fallback if TextCleaner not available
        full_text = doc.content or doc.extracted_text or ""
        # Use LLM for enrichment when API key is present, otherwise rule-based
        use_llm = bool(settings.GROQ_API_KEY)
        logger.info(f"Using {'LLM-based' if use_llm else 'rule-based'} enrichment")
        enriched_requirements = requirement_organizer.organize_and_enrich(
            requirements=cleaned_requirements,
            full_text=full_text,
            use_llm=use_llm
        )
        
        # Update requirements with enrichment data
        updated_count = 0
        import json
        for i, enriched_req in enumerate(enriched_requirements):
            if i < len(requirements):
                req = requirements[i]
                print(f"Updating requirement {req.req_identifier}:")
                print(f"  - Category: {enriched_req.get('category')}")
                print(f"  - Module: {enriched_req.get('module_name')}")
                print(f"  - Semantic ID: {enriched_req.get('semantic_id')}")
                
                # Update fields
                req.semantic_id = enriched_req.get("semantic_id")
                req.module_name = enriched_req.get("module_name", "General")
                req.category = enriched_req.get("category", "functional")
                req.category_confidence = enriched_req.get("category_confidence", 0.5)
                
                # Update JSON fields
                actors = enriched_req.get("actors", [])
                modal_verbs = enriched_req.get("modal_verbs", [])
                vague_terms = enriched_req.get("vague_terms", [])
                
                req.actors_json = json.dumps(actors) if actors else json.dumps([])
                req.modal_verbs_json = json.dumps(modal_verbs) if modal_verbs else json.dumps([])
                req.vague_terms_json = json.dumps(vague_terms) if vague_terms else json.dumps([])
                updated_count += 1
        
        # Commit changes and verify
        try:
            await db.commit()
            print(f"Successfully committed {updated_count} requirements")
            
            # Verify the update by checking the first requirement
            result = await db.execute(select(Requirement).filter(Requirement.doc_id == doc_id))
            first_req = result.scalar_one_or_none()
            if first_req:
                print(f"Verification - First requirement after commit:")
                print(f"  - Category: {first_req.category}")
                print(f"  - Module: {first_req.module_name}")
                print(f"  - Semantic ID: {first_req.semantic_id}")
            
        except Exception as commit_error:
            print(f"Commit failed: {commit_error}")
            await db.rollback()
            raise HTTPException(500, f"Database commit failed: {str(commit_error)}")
        
        return {
            "message": "Document enrichment completed successfully",
            "requirements_updated": len(requirements),
            "enrichment_applied": updated_count
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Error enriching document: {str(e)}")


@router.post("/fix-document/{doc_id}")
async def fix_document_endpoint(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Fix existing document with repeated words and uncategorized requirements"""
    try:
        # Get document
        result = await db.execute(
            select(RequirementDocument).filter(RequirementDocument.doc_id == doc_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(404, "Document not found")
        
        # Get requirements
        result = await db.execute(
            select(Requirement).filter(Requirement.doc_id == doc_id)
        )
        requirements = result.scalars().all()
        
        # Apply text cleaning using global import
        if TextCleaner:
            cleaner = TextCleaner()
        else:
            cleaner = None  # Fallback if TextCleaner not available
        updated_count = 0
        
        for req in requirements:
            if req.original_text and cleaner:
                cleaned_text = cleaner.clean_requirement_text(req.original_text)
                if cleaned_text != req.original_text:
                    req.original_text = cleaned_text
                    req.current_text = cleaned_text
                    updated_count += 1
        
        # Apply enrichment
        from services.ai.requirement_organizer import RequirementOrganizer
        organizer = RequirementOrganizer()
        
        # Create requirement objects for enrichment
        req_objects = []
        for req in requirements:
            req_objects.append({
                "req_id": req.req_id,
                "doc_id": req.doc_id,
                "project_id": req.project_id,
                "req_identifier": req.req_identifier,
                "original_text": req.original_text,
                "current_text": req.current_text,
                "word_count": req.word_count,
                "sequence_order": req.sequence_order,
            })
        
        cleaned_requirements = cleaner.clean_requirements_batch(req_objects) if cleaner else req_objects
        full_text = "\n\n".join(req["original_text"] for req in cleaned_requirements)
        # Use LLM for enrichment when API key is present, otherwise rule-based
        use_llm = bool(settings.GROQ_API_KEY)
        logger.info(f"Using {'LLM-based' if use_llm else 'rule-based'} fix enrichment")
        enriched_requirements = organizer.organize_and_enrich(
            requirements=cleaned_requirements,
            full_text=full_text,
            use_llm=use_llm
        )
        
        # Update requirements with enrichment data
        for i, enriched_req in enumerate(enriched_requirements):
            if i < len(requirements):
                req = requirements[i]
                req.semantic_id = enriched_req.get("semantic_id")
                req.module_name = enriched_req.get("module_name")
                req.category = enriched_req.get("category")
                req.category_confidence = enriched_req.get("category_confidence", 0.5)
                
                # Update JSON fields
                import json
                actors = enriched_req.get("actors", [])
                modal_verbs = enriched_req.get("modal_verbs", [])
                vague_terms = enriched_req.get("vague_terms", [])
                
                req.actors_json = json.dumps(actors) if actors else req.actors_json
                req.modal_verbs_json = json.dumps(modal_verbs) if modal_verbs else req.modal_verbs_json
                req.vague_terms_json = json.dumps(vague_terms) if vague_terms else req.vague_terms_json
        
        await db.commit()
        
        return {
            "message": "Document fixed successfully",
            "requirements_updated": len(requirements),
            "text_cleaning_improvements": updated_count,
            "enrichment_applied": len(enriched_requirements)
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Error fixing document: {str(e)}")


@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete a document and all associated analysis data.
    Implements REQ_07: Project Data Management (GDPR Right to be Forgotten).
    """
    # Load document with relationships needed for counting
    stmt = (
        select(RequirementDocument)
        .where(
            RequirementDocument.doc_id == doc_id,
            RequirementDocument.uploaded_by == current_user.user_id,
        )
        .options(selectinload(RequirementDocument.requirements))
        .options(selectinload(RequirementDocument.validation_sessions))
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    req_count = len(doc.requirements)
    val_count = len(doc.validation_sessions)

    # Refund storage quota
    if doc.file_size_bytes:
        user_result = await db.execute(select(User).filter(User.user_id == current_user.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.storage_used_bytes = max(0, user.storage_used_bytes - doc.file_size_bytes)
            await db.commit()

    # SQLAlchemy cascade handles deletion of requirements, validation_sessions, defects
    await db.delete(doc)
    await db.commit()

    return DocumentDeleteResponse(
        message="Document and all associated data permanently deleted",
        doc_id=doc_id,
        deleted_requirements=req_count,
        deleted_validations=val_count,
    )


@router.post("/{doc_id}/traceability-notes")
async def add_traceability_note(
    doc_id: str,
    note_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a traceability note to a document/requirement.
    Implements BR-16: User notes field with timestamp.
    """
    try:
        # Verify document exists and user has access
        stmt = (
            select(RequirementDocument)
            .join(Project)
            .where(
                RequirementDocument.doc_id == doc_id,
                Project.owner_id == current_user.user_id,
            )
        )
        result = await db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )
        
        # Get requirement_id from note_data
        req_id = note_data.get("req_id")
        if not req_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Requirement ID is required"
            )
        
        # Verify requirement exists in the document
        req_stmt = select(Requirement).where(
            Requirement.req_id == req_id,
            Requirement.doc_id == doc_id
        )
        req_result = await db.execute(req_stmt)
        req = req_result.scalar_one_or_none()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Requirement not found in this document"
            )
        
        # Create note entry
        from models.traceability import TraceabilityNote
        
        note = TraceabilityNote(
            req_id=req_id,
            created_by=current_user.user_id,
            project_id=doc.project_id,
            content=note_data.get("note", ""),
            note_type="user_annotation",
            created_at=_now_iso()
        )
        
        db.add(note)
        await db.commit()
        await db.refresh(note)
        
        return {
            "message": "Traceability note added successfully",
            "note_id": note.note_id,
            "timestamp": note.created_at
        }
        
    except Exception as e:
        logger.error(f"Error adding traceability note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add traceability note"
        )