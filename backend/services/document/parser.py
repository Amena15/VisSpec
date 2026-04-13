"""Document parsing service for PDF and DOCX files."""
import io
from typing import Dict, Any, Optional, List


class DocumentParser:
    """Parses PDF and DOCX documents to extract text and structure."""

    def parse_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Parse a PDF file and extract text, page count, metadata."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()

            result = {
                "filename": filename,
                "file_extension": "pdf",
                "text": text,
                "page_count": len(doc),
                "word_count": len(text.split()),
                "is_scanned_pdf": self._detect_scanned(doc),
                "extracted_author": doc.metadata.get("author", ""),
                "extracted_version": doc.metadata.get("modDate", ""),
            }
            doc.close()
            return result
        except ImportError:
            return {"error": "PyMuPDF not installed. Run: pip install PyMuPDF"}
        except Exception as e:
            return {"error": str(e)}

    def parse_docx(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Parse a DOCX file and extract text and metadata."""
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_content))
            text = "\n".join(p.text for p in doc.paragraphs)

            return {
                "filename": filename,
                "file_extension": "docx",
                "text": text,
                "page_count": None,  # DOCX doesn't have fixed pages
                "word_count": len(text.split()),
                "is_scanned_pdf": 0,
                "extracted_author": doc.core_properties.author or "",
                "extracted_version": str(doc.core_properties.revision or ""),
            }
        except ImportError:
            return {"error": "python-docx not installed. Run: pip install python-docx"}
        except Exception as e:
            return {"error": str(e)}

    def parse_txt(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Parse a plain text file."""
        text = file_content.decode("utf-8", errors="replace")
        return {
            "filename": filename,
            "file_extension": "txt",
            "text": text,
            "page_count": None,
            "word_count": len(text.split()),
            "is_scanned_pdf": 0,
            "extracted_author": "",
            "extracted_version": "",
        }

    def parse(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Auto-detect format and parse the document."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == "pdf":
            return self.parse_pdf(file_content, filename)
        elif ext == "docx":
            return self.parse_docx(file_content, filename)
        elif ext == "txt":
            return self.parse_txt(file_content, filename)
        else:
            return {"error": f"Unsupported file format: .{ext}"}

    @staticmethod
    def _detect_scanned(pdf_doc) -> int:
        """Detect if a PDF is scanned (contains images but little text)."""
        total_text = sum(len(page.get_text().strip()) for page in pdf_doc)
        return 1 if total_text < 100 else 0
