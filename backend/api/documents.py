"""Document upload and management API routes.

Implements REQ_04 (Document Upload), REQ_05 (Text Extraction & Parsing),
REQ_06 (Structure Identification), and REQ_07 (Project Data Management).
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from models.user import User
from models.project import Project
from models.document import RequirementDocument
from models.requirement import Requirement
from schemas.document import (
    DocumentUploadResponse,
    DocumentSummary,
    DocumentDetail,
    DocumentDeleteResponse,
)
from services.document.parser import DocumentParser
from utils.security import get_current_active_user
from config.database import get_db
from core.config import settings
from core.logging import get_logger

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


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
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
            detail=f"Unsupported file format: .{ext}. Only PDF, DOCX, and TXT are accepted.",
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
            detail=f"File too large. Maximum size is {max_size // (1024 * 1024)}MB.",
        )

    # ------------------------------------------------------------------
    # 3. Check user storage quota (NFR_SP1)
    # ------------------------------------------------------------------
    new_usage = current_user.storage_used_bytes + file_size
    quota_bytes = current_user.storage_quota_mb * 1024 * 1024
    
    if new_usage > quota_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Storage quota exceeded. Quota: {current_user.storage_quota_mb}MB, Used: {current_user.storage_used_bytes / (1024 * 1024):.1f}MB, File: {file_size / (1024 * 1024):.1f}MB",
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
                    detail="PDF processing library not available. Please contact support."
                )
            elif "python-docx not installed" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="DOCX processing library not available. Please contact support."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Document parsing failed: {error_msg}"
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
    # 5. Check for scanned PDF with no readable text (outside try-catch)
    # ------------------------------------------------------------------
    is_scanned_pdf = parse_result.get("is_scanned_pdf", 0)
    if is_scanned_pdf == 1 or len(extracted_text.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text detected. Please upload a searchable PDF."
        )
    
    # Extract requirements
    requirements = parser.extract_requirements(extracted_text)
    requirements_count = len(requirements)
    
    # Apply text cleaning to fix repeated words (willwill -> will, etc.)
    try:
        from services.ai.text_cleaner import TextCleaner
        logger.info(f"Applying text cleaning to {len(requirements)} requirements")
        
        # Clean requirements batch
        cleaned_requirements = TextCleaner.clean_requirements_batch(requirements)
        requirements = cleaned_requirements
        
        # Also clean the main document text
        cleaned_extracted_text = TextCleaner.clean_requirement_text(extracted_text)
        
        # Log cleaning results
        if cleaned_extracted_text != extracted_text:
            logger.info("Document text was cleaned during upload")
            logger.debug(f"Original length: {len(extracted_text)}, Cleaned length: {len(cleaned_extracted_text)}")
        
        extracted_text = cleaned_extracted_text
        
        logger.info(f"Text cleaning completed successfully for {len(requirements)} requirements")
        
    except Exception as e:
        logger.error(f"Text cleaning failed during upload: {e}")
        # Continue with original requirements if cleaning fails
        logger.warning("Proceeding with original text due to cleaning failure")
    
    # Identify logical sections
    sections = parser.identify_structure(extracted_text)
    sections_count = len(sections)
    sections_titles = [section["title"] for section in sections]
    
    # Generate document ID and save to database
    doc_id = str(uuid.uuid4())
    
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
        is_scanned_pdf=parse_result.get("is_scanned_pdf", 0),
        extracted_author=parse_result.get("extracted_author"),
        extracted_version=parse_result.get("extracted_version"),
    )
    
    # Save document to database
    db.add(document)
    db.commit()
    
    # Update user storage usage
    current_user.storage_used_bytes = new_usage
    db.commit()
    
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
    
    db.commit()
    
    # Auto-organize requirements for new document (professional flow)
    try:
        logger.info("Auto-organizing requirements for new document")
        req_objects = db.query(Requirement).filter(Requirement.doc_id == doc_id).all()
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
        from services.ai.text_cleaner import TextCleaner
        cleaned_reqs = TextCleaner.clean_requirements_batch(raw_reqs)
        full_text = extracted_text
        enriched_reqs = requirement_organizer.organize_and_enrich(cleaned_reqs, full_text, use_llm=False)
        
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
        db.commit()
        logger.info(f"Auto-organized {updated} requirements")
    except Exception as e:
        logger.warning(f"Auto-organize failed: {e} - manual fix available")
    
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
        upload_date=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


@router.get("/", response_model=List[DocumentSummary])
def list_documents(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all documents for the authenticated user, optionally filtered by project."""
    try:
        # Get documents directly without complex joins first
        docs = db.query(RequirementDocument).filter(
            RequirementDocument.uploaded_by == current_user.user_id
        ).order_by(RequirementDocument.upload_date.desc()).all()

        result = []
        for d in docs:
            # Get requirements count safely
            try:
                req_count = len(d.requirements) if d.requirements else 0
            except:
                req_count = 0

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
                )
            )
        return result
    except Exception as e:
        print(f"Error in documents API: {e}")
        # Return empty list as fallback
        return []


@router.get("/{doc_id}")
def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a single document with its extracted requirements."""
    try:
        # Simplified query to avoid SQLAlchemy errors
        doc = db.query(RequirementDocument).filter(
            RequirementDocument.doc_id == doc_id
        ).first()
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )
        
        # Simple ownership check
        if doc.uploaded_by != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )
        
        # Extract structure from document content
        from services.document.parser import DocumentParser
        parser = DocumentParser()
        sections_data = parser.identify_structure(doc.content or "")
        
        # Get requirements for this document
        requirements = db.query(Requirement).filter(
            Requirement.doc_id == doc_id
        ).order_by(Requirement.sequence_order).all()
        
        print(f"DEBUG: Found {len(requirements)} requirements for document {doc_id}")
        for i, req in enumerate(requirements[:3]):
            print(f"DEBUG: Req {i+1}: {req.original_text[:50]}...")
        
        # Format requirements for response
        req_list = []
        import json
        for req in requirements:
            # Parse JSON fields
            actors = []
            modal_verbs = []
            vague_terms = []
            
            try:
                if req.actors_json:
                    actors = json.loads(req.actors_json)
                if req.modal_verbs_json:
                    modal_verbs = json.loads(req.modal_verbs_json)
                if req.vague_terms_json:
                    vague_terms = json.loads(req.vague_terms_json)
            except json.JSONDecodeError:
                pass
            
            req_list.append({
                "req_id": req.req_id,
                "req_identifier": str(req.req_identifier) if req.req_identifier else "",
                "original_text": str(req.original_text) if req.original_text else "",
                "current_text": str(req.current_text) if req.current_text else "",
                "word_count": req.word_count or 0,
                "sequence_order": req.sequence_order or 0,
                # Enriched fields
                "category": req.category,
                "module_name": req.module_name,
                "semantic_id": req.semantic_id,
                "category_confidence": req.category_confidence,
                "actors": actors,
                "modal_verbs": modal_verbs,
                "vague_terms": vague_terms,
                "validation_status": req.validation_status,
                "upload_date": req.created_at,  # Add creation date for frontend display
            })
        
        from fastapi import Response
        
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
            "upload_date": doc.upload_date if doc.upload_date else "",
            "uploaded_by": doc.uploaded_by,
            "is_scanned_pdf": doc.is_scanned_pdf,
            "extracted_author": doc.extracted_author,
            "extracted_version": doc.extracted_version,
            "sections": sections_data,
            "sections_found": [str(s.get("title", "")) for s in sections_data],
            "requirements": req_list,
        }
        
        # Ensure all data is JSON serializable
        try:
            import json
            json_str = json.dumps(response_data)
            # Add cache-control headers to prevent browser caching
            return Response(
                content=json_str,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "Content-Type": "application/json",
                }
            )
        except (TypeError, ValueError) as json_error:
            print(f"JSON serialization error: {json_error}")
            # Return minimal safe response
            safe_response = {
                "doc_id": doc_id,
                "project_id": str(doc.project_id) if doc.project_id else "",
                "filename": str(doc.filename) if doc.filename else "Document",
                "file_extension": str(doc.file_extension) if doc.file_extension else "txt",
                "file_size_bytes": int(doc.file_size_bytes) if doc.file_size_bytes else 0,
                "word_count": int(doc.word_count) if doc.word_count else 0,
                "page_count": int(doc.page_count) if doc.page_count else 0,
                "status": str(doc.status) if doc.status else "Ready for Analysis",
                "content": "",
                "extracted_text": "",
                "upload_date": "",
                "requirements": [],
            }
            return Response(
                content=json.dumps(safe_response),
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "Content-Type": "application/json",
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_document: {e}")
        # Return a minimal working response
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
async def enrich_document_endpoint(doc_id: str, db: Session = Depends(get_db)):
    """Manually trigger enrichment for existing document"""
    try:
        # Get document
        doc = db.query(RequirementDocument).filter(RequirementDocument.doc_id == doc_id).first()
        if not doc:
            raise HTTPException(404, "Document not found")
        
        # Get requirements
        requirements = db.query(Requirement).filter(Requirement.doc_id == doc_id).all()
        
        if not requirements:
            return {"message": "No requirements found to enrich"}
        
        # Apply enrichment
        from services.ai.requirement_organizer import requirement_organizer
        from services.ai.text_cleaner import TextCleaner
        
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
        
        cleaned_requirements = TextCleaner.clean_requirements_batch(req_objects)
        full_text = doc.content or doc.extracted_text or ""
        enriched_requirements = requirement_organizer.organize_and_enrich(
            requirements=cleaned_requirements,
            full_text=full_text,
            use_llm=False
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
            db.commit()
            print(f"Successfully committed {updated_count} requirements")
            
            # Verify the update by checking the first requirement
            first_req = db.query(Requirement).filter(Requirement.doc_id == doc_id).first()
            if first_req:
                print(f"Verification - First requirement after commit:")
                print(f"  - Category: {first_req.category}")
                print(f"  - Module: {first_req.module_name}")
                print(f"  - Semantic ID: {first_req.semantic_id}")
            
        except Exception as commit_error:
            print(f"Commit failed: {commit_error}")
            db.rollback()
            raise HTTPException(500, f"Database commit failed: {str(commit_error)}")
        
        return {
            "message": "Document enrichment completed successfully",
            "requirements_updated": len(requirements),
            "enrichment_applied": updated_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error enriching document: {str(e)}")


@router.post("/fix-document/{doc_id}")
async def fix_document_endpoint(doc_id: str, db: Session = Depends(get_db)):
    """Fix existing document with repeated words and uncategorized requirements"""
    try:
        # Get document
        doc = db.query(RequirementDocument).filter(RequirementDocument.doc_id == doc_id).first()
        if not doc:
            raise HTTPException(404, "Document not found")
        
        # Get requirements
        requirements = db.query(Requirement).filter(Requirement.doc_id == doc_id).all()
        
        # Apply text cleaning
        from services.ai.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        updated_count = 0
        
        for req in requirements:
            if req.original_text:
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
        
        cleaned_requirements = cleaner.clean_requirements_batch(req_objects)
        full_text = "\n\n".join(req["original_text"] for req in cleaned_requirements)
        enriched_requirements = organizer.organize_and_enrich(
            requirements=cleaned_requirements,
            full_text=full_text,
            use_llm=False
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
        
        db.commit()
        
        return {
            "message": "Document fixed successfully",
            "requirements_updated": len(requirements),
            "text_cleaning_improvements": updated_count,
            "enrichment_applied": len(enriched_requirements)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error fixing document: {str(e)}")


@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete a document and all associated analysis data.
    Implements REQ_07: Project Data Management (GDPR Right to be Forgotten).
    """
    doc = (
        db.query(RequirementDocument)
        .join(Project)
        .filter(
            RequirementDocument.doc_id == doc_id,
            Project.owner_id == current_user.user_id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    req_count = len(doc.requirements)
    val_count = len(doc.validation_sessions)

    # Refund storage quota
    if doc.file_size_bytes:
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        if user:
            user.storage_used_bytes = max(0, user.storage_used_bytes - doc.file_size_bytes)
            db.commit()

    # SQLAlchemy cascade handles deletion of requirements, validation_sessions, defects
    db.delete(doc)
    db.commit()

    return DocumentDeleteResponse(
        message="Document and all associated data permanently deleted",
        doc_id=doc_id,
        deleted_requirements=req_count,
        deleted_validations=val_count,
    )
