"""Document parsing service for PDF, DOCX, and TXT files."""
import io
import re
from typing import Dict, Any, Optional, List, Tuple

from services.ai.text_cleaner import TextCleaner


def _collapse_repeated_word_token(match: re.Match) -> str:
    """Collapse 'willwill' -> 'will' but never touch digit runs like '000' in '25,000'."""
    word = match.group(1)
    if word.isdigit():
        return match.group(0)
    return word


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
        r"^(?:\d+\.)+\s*(?:Overall Description|Product Perspective|Product Features)",
        r"^(?:\d+\.)+\s*(?:Specific Requirements|Functional Requirements|User Requirements)",
        r"^(?:\d+\.)+\s*(?:Other Non-Functional Requirements|Performance Requirements)",
        r"^(?:\d+\.)+\s*(?:Availability Requirements|Reliability|Security|Usability)",
        r"^(?:\d+\.)+\s*(?:Scalability|Maintainability|Portability|Backup)",
        r"^(?:\d+\.)+\s*(?:Business Rules|Summary|Appendices)",
        r"^\d+\.\d+\s+",  # Generic numbered section like 1.1, 3.2
        r"^(?:Chapter|Section)\s+\d+",
        r"^(?:APPENDIX|Appendix)\s+[A-Z]",
        r"^\d+\.\s*[A-Z][a-zA-Z\s]+",  # Main sections like "1. Introduction"
        r"^\d+\.\d+\s*[A-Z][a-zA-Z\s]+",  # Subsections like "2.1 Product Perspective"
    ]
    
    # Fallback patterns for domain-specific or custom section headers
    SECTION_FALLBACK_PATTERNS = [
        r'^[A-Z][A-Z\s]+:$',  # All caps ending with colon (e.g., "INTRODUCTION:")
        r'^[A-Z][a-zA-Z\s]+:$',  # Title case ending with colon (e.g., "Functional Requirements:")
        r'^[A-Z]{3,}$',  # All caps (e.g., "INTRODUCTION")
        r'^\d+\.\s+[A-Z][a-zA-Z]+$',  # Numbered with single word (e.g., "1. Introduction")
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

    def parse_txt(self, file_content, filename: str) -> Dict[str, Any]:
        """Parse a plain text file."""
        # Handle both bytes and string input
        if isinstance(file_content, bytes):
            text = file_content.decode("utf-8", errors="replace")
        else:
            text = str(file_content)
        
        return {
            "filename": filename,
            "file_extension": "txt",
            "text": text,
            "page_count": 1,
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
        Uses fallback patterns for domain-specific headers.
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
            
            # Try primary section patterns first
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
            
            # If not matched by primary patterns, try fallback patterns
            if not is_header:
                for pattern in self.SECTION_FALLBACK_PATTERNS:
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
        Extract requirements from text using improved patterns.
        Properly identifies individual requirement statements.
        Supports multi-line requirements (accumulates until period followed by newline).
        """
        if not text:
            return []
        
        lines = text.split('\n')
        requirements = []
        seq = 0
        current_requirement = None
        
        # Requirement identification patterns - more precise
        req_patterns = [
            # Numbered list items with modal verbs (e.g., "1. The system shall...")
            r'^\s*\d+[\.\)]\s*(?:The\s+system|The\s+application|Users?|Doctor|Patient|Admin|Chemist|Lab|System|User|[A-Z][a-z]*)\s+(?:shall|must|should|will|may)\s+',
            
            # System requirements with modal verbs
            r'\bThe\s+system\s+(?:shall|must|should|will|may)\s+',
            r'\bThe\s+application\s+(?:shall|must|should|will|may)\s+',
            r'\bUsers?\s+(?:shall|must|should|will|may)\s+',
            
            # General requirements with modal verbs
            r'\b(?:shall|must|should|will|may)\s+',
            
            # Requirements with actors/subjects
            r'\b(?:Doctor|Patient|Admin|Chemist|Lab|System|User)\s+(?:shall|must|should|will|may)\s+',
            
            # Requirements with clear subjects
            r'\b[A-Z][a-z]*\s+(?:shall|must|should|will|may)\s+',
        ]
        
        # Non-requirement patterns to skip
        skip_patterns = [
            # Document structure
            r'^(?:\d+\.?\s*)?(?:Introduction|Overview|Summary|Conclusion|Contents?|Table\s+\d+|Figure\s+\d+|Appendix\s+[A-Z]?)\b',
            r'^[A-Z][A-Z\s]+$',
            r'^\s*[=-]{3,}\s*$',
            r'^\s*\d+\.\s*$',
            
            # Lists and references
            r'^\s*[-•*]\s*',
            r'^\s*\d+\)\s*',
            r'^BR-\d+|FR-\d+|NFR-\d+|UC-\d+',
            
            # Meta descriptions
            r'^(?:This\s+document|The\s+following|For\s+this|Word\s+count)',
            r'^\s*(?:All\s+data|Full\s+system|The\s+system|The\s+codebase)',
            
            # Code/configuration patterns
            r'^\s*(def |class |import |from |function |var |let |const )',
        ]
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                # If we have a current requirement being built, save it
                if current_requirement:
                    self._finalize_requirement(current_requirement, requirements, seq)
                    seq += 1
                    current_requirement = None
                continue
            
            # Skip very short lines (unless we're building a multi-line requirement)
            if len(line_stripped) < 8 and not current_requirement:
                continue
            
            # Skip non-requirement patterns
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    should_skip = True
                    break
            
            if should_skip and not current_requirement:
                continue
            
            # Check if line starts a new requirement
            is_requirement_start = False
            for pattern in req_patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    is_requirement_start = True
                    break
            
            if is_requirement_start:
                # Save previous requirement if exists
                if current_requirement:
                    self._finalize_requirement(current_requirement, requirements, seq)
                    seq += 1
                
                # Start new requirement
                current_requirement = {
                    "text": line_stripped,
                    "line_count": 1
                }
            elif current_requirement:
                # Continue building multi-line requirement
                current_requirement["text"] += " " + line_stripped
                current_requirement["line_count"] += 1
                
                # Check if this line ends with a period (end of requirement)
                if line_stripped.endswith('.'):
                    self._finalize_requirement(current_requirement, requirements, seq)
                    seq += 1
                    current_requirement = None
            else:
                # Line doesn't match requirement patterns and we're not building one
                continue

        # Save any remaining requirement
        if current_requirement:
            self._finalize_requirement(current_requirement, requirements, seq)

        return requirements
    
    def _finalize_requirement(self, req_data: Dict[str, Any], requirements: List[Dict[str, Any]], seq: int):
        """Finalize and add a requirement to the list."""
        cleaned_text = re.sub(r'\s+', ' ', req_data["text"])  # Normalize whitespace
        cleaned_text = re.sub(r'\.+$', '', cleaned_text)  # Remove trailing period
        
        # Try to find requirement ID
        req_id = None
        for pattern in self.REQ_ID_PATTERNS:
            match = re.search(pattern, cleaned_text, re.IGNORECASE)
            if match:
                req_id = match.group(1).upper()
                break

        requirements.append({
            "req_identifier": req_id or f"REQ-{seq+1:03d}",
            "original_text": cleaned_text,
            "word_count": len(cleaned_text.split()),
            "sequence_order": seq,
        })

    def sanitize_text(self, text: str) -> str:
        """Sanitize extracted text for storage and search."""
        if not text:
            return ""
        
        # Remove duplicate consecutive words with space (conservative approach)
        # Only matches "will will" not "willwill" to avoid false positives
        # Also catches triple repeats (will will will -> will)
        text = re.sub(r'\b(\w+)(?:\s+\1)+\b', r'\1', text, flags=re.IGNORECASE)
        
        # Modal verbs jammed without space (e.g. shallwill) — \b between modals does not match
        text = TextCleaner.fix_concatenated_modals(text)
        
        # Handle concatenated duplicates (willwill -> will); skip digit-only tokens (preserves 25,000)
        text = re.sub(r'\b(\w+)(\1)+\b', _collapse_repeated_word_token, text, flags=re.IGNORECASE)
        
        # Remove page numbers (but preserve section headers)
        # Page numbers are typically standalone or at the end of lines
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # Standalone numbers
        text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)  # "Page 1 of 3"
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)  # Numbers alone on lines
        
        # Remove multiple newlines but preserve single newlines
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Remove extra spaces but preserve newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Only spaces and tabs, not newlines
        
        return text.strip()

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
        result["extracted_text"] = cleaned_text

        # Step 3: Structure identification (REQ_06)
        sections = self.identify_structure(cleaned_text)
        result["sections"] = sections
        result["sections_found"] = [s["title"] for s in sections]

        # Step 4: Requirement extraction (REQ_05)
        requirements = self.extract_requirements(cleaned_text)
        result["requirements"] = requirements
        result["requirements_found"] = len(requirements)

        return result

