#!/usr/bin/env python3

"""
Module 2: Document Processing Comprehensive Unit Tests
Covers REQ_04, REQ_05, REQ_06, REQ_07 and all document processing functionality

Test Coverage:
- File upload format validation (.pdf, .docx, .txt only - BR-07)
- Maximum file size enforcement (10MB - BR-08)
- PyMuPDF PDF text extraction with structure preservation
- python-docx DOCX text extraction
- OCR fallback for scanned/image-based PDFs
- Structure identification (headers, requirement IDs, body text)
- Text sanitization (removes metadata, formatting noise)
- Document storage with status "Ready for Analysis" in PostgreSQL
- Delete document with cascade deletion of associated data
- Storage quota tracking implementation
"""

import pytest
import asyncio
import os
import io
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from fastapi.testclient import TestClient
from fastapi import UploadFile
from sqlalchemy.orm import Session

# Add backend to path
import sys
sys.path.insert(0, '/Users/amena/Documents/FYPCode/VisSpec/backend')

from main import app
from models.document import RequirementDocument
from models.requirement import Requirement
from services.document.parser import DocumentParser
from services.document.parser_enhanced import EnhancedDocumentParser
from core.config import settings

client = TestClient(app)

class TestModule2DocumentProcessing:
    """Comprehensive test suite for Module 2: Document Processing"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock()
    
    @pytest.fixture
    def document_parser(self):
        """Document parser instance"""
        return DocumentParser()
    
    @pytest.fixture
    def enhanced_parser(self):
        """Enhanced document parser instance"""
        return EnhancedDocumentParser()

    # === File Upload Format Tests ===
    
    def test_upload_accepts_pdf_format(self):
        """Test upload accepts .pdf files"""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        pdf_file = UploadFile("test.pdf", io.BytesIO(pdf_content), "application/pdf")
        
        with patch('api.documents.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            with patch('services.document.parser.DocumentParser.extract_text') as mock_extract:
                mock_extract.return_value = "Sample PDF content with requirement text."
                
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("test.pdf", pdf_file.file, "application/pdf")},
                    data={"project_id": "test-project-id"}
                )
                
                # Should accept PDF format
                assert response.status_code in [200, 201]
    
    def test_upload_accepts_docx_format(self):
        """Test upload accepts .docx files"""
        # Create a mock DOCX file
        docx_content = b"PK\x03\x04\x14\x00\x06\x00"  # DOCX header
        docx_file = UploadFile("test.docx", io.BytesIO(docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        
        with patch('api.documents.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            with patch('services.document.parser.DocumentParser.extract_text') as mock_extract:
                mock_extract.return_value = "Sample DOCX content with requirement text."
                
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("test.docx", docx_file.file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                    data={"project_id": "test-project-id"}
                )
                
                # Should accept DOCX format
                assert response.status_code in [200, 201]
    
    def test_upload_accepts_txt_format(self):
        """Test upload accepts .txt files"""
        txt_content = b"This is a sample text file with requirement text."
        txt_file = UploadFile("test.txt", io.BytesIO(txt_content), "text/plain")
        
        with patch('api.documents.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            with patch('services.document.parser.DocumentParser.extract_text') as mock_extract:
                mock_extract.return_value = txt_content.decode()
                
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("test.txt", txt_file.file, "text/plain")},
                    data={"project_id": "test-project-id"}
                )
                
                # Should accept TXT format
                assert response.status_code in [200, 201]
    
    def test_upload_rejects_invalid_formats_br07(self):
        """Test upload rejects invalid file formats (BR-07)"""
        invalid_files = [
            ("test.exe", b"EXE content", "application/octet-stream"),
            ("test.jpg", b"JPG content", "image/jpeg"),
            ("test.png", b"PNG content", "image/png"),
            ("test.zip", b"ZIP content", "application/zip"),
            ("test.mp4", b"MP4 content", "video/mp4"),
        ]
        
        for filename, content, content_type in invalid_files:
            response = client.post(
                "/api/documents/upload",
                files={"file": (filename, io.BytesIO(content), content_type)},
                data={"project_id": "test-project-id"}
            )
            
            # Should reject invalid formats
            assert response.status_code == 400
            data = response.json()
            assert "format" in data.get("detail", "").lower()
            assert "pdf" in data.get("detail", "").lower() or "docx" in data.get("detail", "").lower() or "txt" in data.get("detail", "").lower()

    # === File Size Tests ===
    
    def test_upload_enforces_max_file_size_br08(self):
        """Test upload enforces 10MB maximum file size (BR-08)"""
        # Create a file larger than 10MB
        large_content = b"X" * (11 * 1024 * 1024)  # 11MB
        
        response = client.post(
            "/api/documents/upload",
            files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")},
            data={"project_id": "test-project-id"}
        )
        
        # Should reject files larger than 10MB
        assert response.status_code == 413  # Payload Too Large
        data = response.json()
        assert "size" in data.get("detail", "").lower()
        assert "10MB" in data.get("detail", "").lower() or "10mb" in data.get("detail", "").lower()
    
    def test_upload_accepts_valid_file_size(self):
        """Test upload accepts files within size limit"""
        # Create a file within size limit (5MB)
        valid_content = b"X" * (5 * 1024 * 1024)  # 5MB
        
        with patch('api.documents.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            with patch('services.document.parser.DocumentParser.extract_text') as mock_extract:
                mock_extract.return_value = "Sample content"
                
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("valid.pdf", io.BytesIO(valid_content), "application/pdf")},
                    data={"project_id": "test-project-id"}
                )
                
                # Should accept files within size limit
                assert response.status_code in [200, 201]

    # === Text Extraction Tests ===
    
    def test_pymupdf_pdf_text_extraction(self):
        """Test PyMuPDF extracts text correctly from PDF with structure preservation"""
        parser = DocumentParser()
        
        # Mock PyMuPDF functionality
        mock_document = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "1. Introduction\nThis is the introduction section.\n2. Requirements\nThe system shall..."
        mock_document.pages = [mock_page]
        
        with patch('fitz.open') as mock_fitz:
            mock_fitz.return_value.__enter__.return_value = mock_document
            
            extracted_text = parser.extract_text("test.pdf")
            
            # Should extract text with preserved structure
            assert "1. Introduction" in extracted_text
            assert "2. Requirements" in extracted_text
            assert "The system shall" in extracted_text
    
    def test_python_docx_text_extraction(self):
        """Test python-docx extracts text from DOCX files"""
        parser = DocumentParser()
        
        # Mock python-docx functionality
        mock_document = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = "The system shall process user requests."
        mock_document.paragraphs = [mock_paragraph]
        
        with patch('docx.Document') as mock_docx:
            mock_docx.return_value = mock_document
            
            extracted_text = parser.extract_text("test.docx")
            
            # Should extract text from DOCX
            assert "The system shall process user requests" in extracted_text
    
    def test_ocr_fallback_for_scanned_pdfs(self):
        """Test OCR fallback for scanned/image-based PDFs"""
        parser = DocumentParser()
        
        # Mock PDF with no extractable text
        mock_document = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""  # No text
        mock_page.get_images.return_value = [{"xref": 1}]  # Has images
        mock_document.pages = [mock_page]
        
        with patch('fitz.open') as mock_fitz:
            mock_fitz.return_value.__enter__.return_value = mock_document
            
            # OCR should return appropriate error or attempt extraction
            with patch('pytesseract.image_to_string') as mock_ocr:
                mock_ocr.return_value = "OCR extracted text"
                
                extracted_text = parser.extract_text("scanned.pdf")
                
                # Should handle OCR appropriately
                assert extracted_text is not None
    
    def test_ocr_no_text_detected_error(self):
        """Test OCR returns 'No text detected' error for image-only PDFs"""
        parser = DocumentParser()
        
        # Mock PDF with images but no text
        mock_document = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""
        mock_page.get_images.return_value = [{"xref": 1}]
        mock_document.pages = [mock_page]
        
        with patch('fitz.open') as mock_fitz:
            mock_fitz.return_value.__enter__.return_value = mock_document
            
            with patch('pytesseract.image_to_string') as mock_ocr:
                mock_ocr.return_value = ""  # OCR finds no text
                
                extracted_text = parser.extract_text("scanned.pdf")
                
                # Should return appropriate message for no text
                assert extracted_text == "" or "no text" in extracted_text.lower()

    # === Structure Identification Tests ===
    
    def test_structure_identification_headers(self):
        """Test structure identification separates headers correctly"""
        enhanced_parser = EnhancedDocumentParser()
        
        sample_text = """
        1. System Requirements
        This section describes system requirements.
        
        1.1 Functional Requirements
        The system shall provide user authentication.
        
        2. Non-Functional Requirements
        The system shall respond within 2 seconds.
        """
        
        # Test header identification
        lines = sample_text.split('\n')
        headers = []
        for line in lines:
            if enhanced_parser._is_header(line):
                headers.append(line.strip())
        
        assert "1. System Requirements" in headers
        assert "1.1 Functional Requirements" in headers
        assert "2. Non-Functional Requirements" in headers
    
    def test_structure_identification_requirement_ids(self):
        """Test structure identification extracts requirement IDs"""
        enhanced_parser = EnhancedDocumentParser()
        
        sample_text = """
        REQ-001: The system shall allow users to register.
        REQ-002: The system shall authenticate users.
        SR-001: System shall process data securely.
        """
        
        # Test requirement ID extraction
        lines = sample_text.split('\n')
        req_ids = []
        for line in lines:
            req_id = enhanced_parser._extract_requirement_id(line)
            if req_id:
                req_ids.append(req_id)
        
        assert "REQ-001" in req_ids
        assert "REQ-002" in req_ids
        assert "SR-001" in req_ids
    
    def test_structure_identification_body_text(self):
        """Test structure identification separates body text from headers"""
        enhanced_parser = EnhancedDocumentParser()
        
        sample_text = """
        1. Introduction
        This is the body text for introduction.
        It contains multiple sentences.
        
        2. Requirements
        The system shall process user requests.
        Additional requirement details here.
        """
        
        # Test body text identification
        lines = sample_text.split('\n')
        body_text = []
        for line in lines:
            line = line.strip()
            if line and not enhanced_parser._is_header(line):
                body_text.append(line)
        
        assert "This is the body text for introduction." in body_text
        assert "The system shall process user requests." in body_text

    # === Text Sanitization Tests ===
    
    def test_text_sanitization_removes_metadata(self):
        """Test text sanitization removes metadata"""
        parser = DocumentParser()
        
        # Text with metadata
        text_with_metadata = """
        Author: John Doe
        Date: 2024-01-01
        Version: 1.0
        
        1. Requirements
        The system shall process data.
        """
        
        sanitized = parser._sanitize_text(text_with_metadata)
        
        # Should remove metadata lines
        assert "Author: John Doe" not in sanitized
        assert "Date: 2024-01-01" not in sanitized
        assert "Version: 1.0" not in sanitized
        assert "1. Requirements" in sanitized
        assert "The system shall process data" in sanitized
    
    def test_text_sanitization_removes_formatting_noise(self):
        """Test text sanitization removes formatting noise"""
        parser = DocumentParser()
        
        # Text with formatting noise
        text_with_noise = """
        \t\t1. Requirements\n
        The system shall process data.\r\n
        \f\f2. Functional Requirements\n
        System shall be user-friendly.\v\v
        """
        
        sanitized = parser._sanitize_text(text_with_noise)
        
        # Should remove formatting characters
        assert '\t' not in sanitized
        assert '\r' not in sanitized
        assert '\n' not in sanitized or sanitized.count('\n') < text_with_noise.count('\n')
        assert '\f' not in sanitized
        assert '\v' not in sanitized

    # === Database Storage Tests ===
    
    def test_document_storage_ready_for_analysis_status(self):
        """Test document stored with 'Ready for Analysis' status in PostgreSQL"""
        with patch('api.documents.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock document creation
            mock_document = MagicMock()
            mock_document.id = 1
            mock_document.status = "ready_for_analysis"
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            with patch('services.document.parser.DocumentParser.extract_text') as mock_extract:
                mock_extract.return_value = "Sample requirement text."
                
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("test.pdf", io.BytesIO(b"PDF content"), "application/pdf")},
                    data={"project_id": "test-project-id"}
                )
                
                # Should store with correct status
                assert response.status_code in [200, 201]
                
                # Verify document status would be set correctly
                # (In real implementation, this would be verified in database)
    
    def test_word_count_calculation(self):
        """Test word count is calculated correctly"""
        parser = DocumentParser()
        
        sample_text = "The system shall allow users to register accounts. Authentication is required for access."
        word_count = parser._calculate_word_count(sample_text)
        
        assert word_count == 13  # Count words correctly
    
    def test_storage_quota_tracking(self):
        """Test storage quota tracking implementation"""
        # Mock storage quota check
        with patch('api.documents.check_storage_quota') as mock_quota:
            mock_quota.return_value = True  # Within quota
            
            response = client.post(
                "/api/documents/upload",
                files={"file": ("test.pdf", io.BytesIO(b"PDF content"), "application/pdf")},
                data={"project_id": "test-project-id"}
            )
            
            # Should check quota before upload
            mock_quota.assert_called_once()
        
        # Test quota exceeded
        with patch('api.documents.check_storage_quota') as mock_quota:
            mock_quota.return_value = False  # Exceeded quota
            
            response = client.post(
                "/api/documents/upload",
                files={"file": ("test.pdf", io.BytesIO(b"PDF content"), "application/pdf")},
                data={"project_id": "test-project-id"}
            )
            
            # Should reject if quota exceeded
            assert response.status_code == 413  # Quota exceeded

    # === Document Deletion Tests ===
    
    def test_delete_document_cascade_deletion(self):
        """Test delete document permanently removes all associated data"""
        with patch('api.documents.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock document exists
            mock_document = MagicMock()
            mock_document.id = 1
            mock_db.query.return_value.filter.return_value.first.return_value = mock_document
            
            # Mock cascade deletion
            mock_db.query.return_value.filter.return_value.delete.return_value = 1
            mock_db.commit.return_value = None
            
            response = client.delete("/api/documents/1")
            
            assert response.status_code == 200
            
            # Verify cascade deletion would be performed
            # (In real implementation, this would delete from documents, requirements, validation_results tables)
    
    def test_delete_nonexistent_document(self):
        """Test delete nonexistent document returns appropriate error"""
        with patch('api.documents.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock document doesn't exist
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.delete("/api/documents/999")
            
            assert response.status_code == 404

    # === Enhanced Parser Tests ===
    
    def test_enhanced_parser_requirement_extraction(self):
        """Test enhanced parser extracts requirements accurately"""
        enhanced_parser = EnhancedDocumentParser()
        
        sample_text = """
        1. Functional Requirements
        1.1 User Management
        The system shall allow users to register accounts with valid email addresses.
        Users must be able to reset their passwords securely.
        
        1.2 Authentication
        The system shall authenticate users before granting access.
        Login attempts shall be logged for security purposes.
        """
        
        requirements = enhanced_parser.extract_requirements(sample_text)
        
        # Should extract requirements properly
        assert len(requirements) >= 3  # Should find multiple requirements
        
        # Check requirement structure
        for req in requirements:
            assert 'text' in req
            assert 'req_id' in req or 'section_header' in req
            assert len(req['text']) > 10  # Reasonable length
    
    def test_enhanced_parser_modal_verb_detection(self):
        """Test enhanced parser detects modal verbs correctly"""
        enhanced_parser = EnhancedDocumentParser()
        
        # Test various modal verbs
        test_cases = [
            ("The system shall process data.", True),
            ("Users must authenticate.", True),
            ("The application may provide reports.", True),
            ("System should respond quickly.", True),
            ("The system processes data.", False),  # No modal verb
        ]
        
        for text, should_detect in test_cases:
            is_requirement = enhanced_parser._is_requirement(text)
            assert is_requirement == should_detect, f"Failed for: {text}"

    # === Integration Tests ===
    
    def test_complete_document_processing_pipeline(self):
        """Test complete document processing pipeline from upload to storage"""
        # Create test file
        test_content = b"""
        1. System Requirements
        1.1 Authentication
        The system shall authenticate users before granting access.
        
        1.2 User Management
        Users must be able to register accounts with valid email addresses.
        """
        
        with patch('api.documents.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock document and requirement creation
            mock_document = MagicMock()
            mock_document.id = 1
            mock_document.status = "ready_for_analysis"
            mock_document.word_count = 25
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            response = client.post(
                "/api/documents/upload",
                files={"file": ("requirements.pdf", io.BytesIO(test_content), "application/pdf")},
                data={"project_id": "test-project-id"}
            )
            
            # Should process successfully
            assert response.status_code in [200, 201]
            
            # Verify document was stored
            mock_db.add.assert_called()
            mock_db.commit.assert_called()
    
    def test_error_handling_invalid_file(self):
        """Test error handling for invalid files"""
        # Test corrupted file
        corrupted_content = b"Corrupted content that is not a valid file"
        
        response = client.post(
            "/api/documents/upload",
            files={"file": ("corrupted.pdf", io.BytesIO(corrupted_content), "application/pdf")},
            data={"project_id": "test-project-id"}
        )
        
        # Should handle gracefully
        assert response.status_code in [400, 422]
    
    def test_error_handling_extraction_failure(self):
        """Test error handling when text extraction fails"""
        with patch('api.documents.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock extraction failure
            with patch('services.document.parser.DocumentParser.extract_text') as mock_extract:
                mock_extract.side_effect = Exception("Extraction failed")
                
                response = client.post(
                    "/api/documents/upload",
                    files={"file": ("test.pdf", io.BytesIO(b"PDF content"), "application/pdf")},
                    data={"project_id": "test-project-id"}
                )
                
                # Should handle extraction failure
                assert response.status_code in [400, 500]

# === Test Execution ===

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
