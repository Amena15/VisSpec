"""Document parsing service for PDF, DOCX, and TXT files."""
import io
import re
from typing import Dict, Any, Optional, List, Tuple


class DocumentParser:
    """Parses PDF and DOCX documents to extract text, structure, and requirements."""

    # Common SRS section headers for structure identification (REQ_06)
    SECTION_PATTERNS = [
        r"^(?:\d+\.)+\s*(?:Functional Requirements|System Overview|Introduction|Scope|Purpose)",
        r"^(?:\d+\.)+\s*(?:Non-Functional Requirements|Performance Requirements|Security Requirements)",
        r"^(?:\d+\.)+\s*(?:Interface Requirements|User Interface|External Interface)",
        r"^(?:\d+\.)+\s*(?:System Features|Use Cases|User Requirements)",
        r"^(?:\d+\.)+\s*(?:Constraints|Assumptions|Dependencies)",
        r"^(?:\d+\.)+\s*(?:Data Requirements|Database|Data Model)",
        r"^\d+\.\d+\s+",  # Generic numbered section like 1.1, 3.2
        r"^(?:Chapter|Section)\s+\d+",
        r"^(?:APPENDIX|Appendix)\s+[A-Z]",
    ]

    # Requirement ID patterns (REQ_05)
    REQ_ID_PATTERNS = [
        r"(REQ[_\-]?\d+)",
        r"(FR[_\-]?\d+)",
        r"(NFR[_\-]?\d+)",
        r"(SR[_\-]?\d+)",
        r"(\d+\.\d+\.\d+)",
        r"(UC[_\-]?\d+)",
    ]

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

    def identify_structure(self, text: str) -> List[Dict[str, Any]]:
        """
        Identify logical sections/headers in the document.
        Implements REQ_06: Structure Identification.
        """
        sections = []
        lines = text.split("\n")
        current_section = None
        section_text = []
        seq = 0

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            is_header = False
            for pattern in self.SECTION_PATTERNS:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    # Save previous section
                    if current_section:
                        sections.append({
                            "title": current_section,
                            "text": "\n".join(section_text).strip(),
                            "sequence_order": seq,
                        })
                    current_section = line_stripped
                    section_text = []
                    seq += 1
                    is_header = True
                    break

            if not is_header and current_section:
                section_text.append(line_stripped)
            elif not is_header and not current_section:
                # Text before first header
                current_section = "Introduction"
                section_text.append(line_stripped)

        # Save last section
        if current_section:
            sections.append({
                "title": current_section,
                "text": "\n".join(section_text).strip(),
                "sequence_order": seq,
            })

        return sections

    def extract_requirements(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract individual requirements from text.
        Identifies requirement IDs, headers, and body text.
        Implements REQ_05: Text Extraction & Parsing.
        """
        requirements = []
        lines = text.split("\n")
        seq = 0

        # More flexible requirement trigger patterns
        req_triggers = [
            r"(?:shall|should|must|will|may)\s+.+",
            r"(?:the\s+)?(?:system|user|application|software|database)\s+(?:shall|should|must|will|may)\s+.+",
            r"(?:patients|doctors|administrators|users)\s+(?:shall|should|must|will|may)\s+.+",
        ]

        # First pass: look for lines with modal verbs
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or len(line_stripped) < 10:
                continue

            # Check if line contains a requirement statement
            is_requirement = False
            for trigger in req_triggers:
                if re.search(trigger, line_stripped, re.IGNORECASE):
                    is_requirement = True
                    break

            if is_requirement:
                # Try to find a requirement ID
                req_id = None
                for pattern in self.REQ_ID_PATTERNS:
                    match = re.search(pattern, line_stripped, re.IGNORECASE)
                    if match:
                        req_id = match.group(1).upper()
                        break

                requirements.append({
                    "req_identifier": req_id or f"REQ-{seq+1:03d}",
                    "original_text": line_stripped,
                    "word_count": len(line_stripped.split()),
                    "sequence_order": seq,
                })
                seq += 1

        # If still no requirements found, do very broad search for modal verbs
        if not requirements:
            seq = 0
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped or len(line_stripped) < 10:
                    continue
                
                # Very broad modal verb search
                if re.search(r'\b(shall|must|should|will|may)\b', line_stripped, re.IGNORECASE):
                    requirements.append({
                        "req_identifier": f"REQ-{seq+1:03d}",
                        "original_text": line_stripped,
                        "word_count": len(line_stripped.split()),
                        "sequence_order": seq,
                    })
                    seq += 1

        return requirements

    def sanitize_text(self, text: str) -> str:
        """
        Remove useless metadata and formatting noise.
        Eliminates page numbers, repeated headers/footers.
        """
        # Remove page numbers like "Page 1 of 10" or just "1"
        text = re.sub(r"\n\s*Page\s+\d+\s+of\s+\d+\s*\n", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

        # Remove repeated header/footer patterns
        lines = text.split("\n")
        cleaned = []
        seen_lines = set()
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Skip if it's a very short repeated line (likely header/footer)
            if len(stripped) < 30 and stripped in seen_lines:
                continue
            seen_lines.add(stripped)
            cleaned.append(stripped)

        return "\n".join(cleaned)

    def parse_full(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Full parsing pipeline: extract text, sanitize, identify structure,
        extract requirements.
        """
        # Step 1: Basic parsing
        result = self.parse(file_content, filename)
        if "error" in result:
            return result

        text = result.get("text", "")

        # Step 2: Sanitize (remove noise)
        cleaned_text = self.sanitize_text(text)
        result["cleaned_text"] = cleaned_text

        # Step 3: Structure identification (REQ_06)
        sections = self.identify_structure(cleaned_text)
        result["sections"] = sections
        result["sections_found"] = [s["title"] for s in sections]

        # Step 4: Requirement extraction (REQ_05)
        requirements = self.extract_requirements(cleaned_text)
        result["requirements"] = requirements
        result["requirements_found"] = len(requirements)

        return result

