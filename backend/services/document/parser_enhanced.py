"""Enhanced document parsing service for professional quality requirement extraction."""

import re
from typing import Dict, Any, Optional, List, Tuple

class EnhancedDocumentParser:
    """Professional quality document parser for VisSpec."""
    
    def __init__(self):
        # Enhanced modal verbs list
        self.MODAL_VERBS = [
            'shall', 'must', 'should', 'will', 'may', 'can', 'could', 'would', 'might'
        ]
        
        # Enhanced action verbs for healthcare domain
        self.ACTION_WORDS = [
            'maintain', 'add', 'create', 'update', 'delete', 'view', 'search', 'manage', 'process',
            'handle', 'generate', 'send', 'receive', 'validate', 'authenticate', 'authorize',
            'login', 'register', 'logout', 'book', 'cancel', 'check', 'provide', 'deliver',
            'prescribe', 'diagnose', 'treat', 'monitor', 'track', 'record', 'store', 'retrieve',
            'display', 'show', 'hide', 'enable', 'disable', 'allow', 'prevent', 'restrict',
            'support', 'facilitate', 'ensure', 'guarantee', 'protect', 'secure', 'backup',
            'archive', 'restore', 'sync', 'syncronize', 'integrate', 'connect', 'disconnect'
        ]
        
        # Healthcare domain subjects
        self.HEALTHCARE_SUBJECTS = [
            'system', 'application', 'user', 'users', 'doctor', 'patient', 'admin', 'lab', 'chemist',
            'clinic', 'hospital', 'staff', 'nurse', 'pharmacist', 'receptionist', 'manager',
            'software', 'database', 'interface', 'module', 'feature', 'prescription', 'medicine',
            'appointment', 'consultation', 'report', 'record', 'history', 'profile', 'account',
            'data', 'information', 'request', 'response', 'notification', 'alert', 'message'
        ]
        
        # Skip patterns for better filtering
        self.SKIP_PATTERNS = [
            r'^\d+\.\d+\s+\w+',  # Section headers like "2.1 User"
            r'^[A-Z][a-z]+\s*\d+',  # Headers like "Figure 1"
            r'^Table\s+\d+',  # Table references
            r'^Page\s+\d+',  # Page numbers
            r'^\d+\s+of\s+\d+',  # Page ranges
            r'^\d+$',  # Standalone numbers
            r'^[A-Z]{2,}\s*\d+',  # Codes like "REQ-001"
            r'^\w+\s*\|\s*\w+',  # Table headers
            r'^\s*$',  # Empty lines
            r'^[ivxlcdm]+\.\s+',  # Roman numerals
        ]
        
        # Professional section patterns
        self.SECTION_PATTERNS = [
            r'^\d+\.\s+[A-Z][a-zA-Z\s]+$',  # "1. Introduction"
            r'^\d+\.\d+\s+[A-Z][a-zA-Z\s]+$',  # "2.1 User Management"
            r'^[A-Z][a-zA-Z\s]+$',  # All caps headers
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:$',  # Headers ending with colon
        ]
    
    def clean_merged_modals(self, text: str) -> str:
        """Enhanced merged modal verb cleanup."""
        # Common merged modal patterns
        merged_patterns = [
            (r'shallshould', 'shall'),
            (r'shallmust', 'shall'),
            (r'shallwill', 'shall'),
            (r'shallmay', 'shall'),
            (r'shallcan', 'shall'),
            (r'shouldshall', 'should'),
            (r'shouldmust', 'should'),
            (r'shouldwill', 'should'),
            (r'mustshall', 'must'),
            (r'mustshould', 'must'),
            (r'mustwill', 'must'),
            (r'willshall', 'will'),
            (r'willshould', 'will'),
            (r'willmust', 'will'),
            (r'willcan', 'will'),
            (r'canshall', 'can'),
            (r'canshould', 'can'),
            (r'canwill', 'can'),
            (r'mayshall', 'may'),
            (r'mayshould', 'may'),
            (r'maywill', 'may'),
        ]
        
        cleaned_text = text
        for pattern, replacement in merged_patterns:
            cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.IGNORECASE)
        
        return cleaned_text
    
    def sanitize_text(self, text: str) -> str:
        """Enhanced text sanitization."""
        if not text:
            return ""
        
        # Step 1: Clean merged modal verbs first
        text = self.clean_merged_modals(text)
        
        # Step 2: Remove duplicate consecutive words
        text = re.sub(r'\b(\w+)(?:\s+\1)+\b', r'\1', text, flags=re.IGNORECASE)
        
        # Step 3: Remove concatenated duplicates (willwill -> will)
        text = re.sub(r'\b(\w+)(\1)+\b', r'\1', text, flags=re.IGNORECASE)
        
        # Step 4: Remove page numbers and headers
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Step 5: Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def extract_requirements(self, text: str) -> List[Dict[str, Any]]:
        """Enhanced requirement extraction for professional quality."""
        # Clean the text first
        cleaned_text = self.sanitize_text(text)
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', cleaned_text)
        requirements = []
        req_counter = 1
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:  # Skip very short sentences
                continue
            
            # Check if it's a requirement
            if self._is_requirement(sentence):
                req_id = f"REQ-{req_counter:03d}"
                word_count = len(sentence.split())
                
                requirement = {
                    "req_identifier": req_id,
                    "original_text": sentence,
                    "current_text": sentence,
                    "word_count": word_count,
                    "sequence_order": req_counter,
                    "category": "functional",  # Will be enhanced later
                    "module_name": "General",  # Will be enhanced later
                    "semantic_id": f"FR-GEN-{req_counter:02d}",
                    "actors_json": [],
                    "modal_verbs_json": [],
                    "vague_terms_json": []
                }
                
                requirements.append(requirement)
                req_counter += 1
        
        return requirements
    
    def _is_requirement(self, sentence: str) -> bool:
        """Enhanced requirement detection logic for professional documents."""
        sentence_lower = sentence.lower()
        
        # Must have modal verb or strong action verb
        has_modal = any(modal in sentence_lower for modal in self.MODAL_VERBS)
        has_action = any(action in sentence_lower for action in self.ACTION_WORDS)
        
        if not (has_modal or has_action):
            return False
        
        # Must have subject (expanded for professional documents)
        has_subject = any(subject in sentence_lower for subject in self.HEALTHCARE_SUBJECTS)
        if not has_subject:
            return False
        
        # Skip if it matches skip patterns
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                return False
        
        # Must be reasonable length (not too short, not too long)
        if len(sentence) < 15 or len(sentence) > 500:
            return False
        
        # Must have minimum complexity (at least 5 words)
        if len(sentence.split()) < 5:
            return False
        
        # Additional professional requirement patterns
        professional_patterns = [
            r'\b(?:the system|the application|users|patients|doctors|admin|staff)\s+(?:shall|must|should|will|may)\s+(?:be|have|provide|allow|enable|support|facilitate|ensure|validate|process|handle|manage|create|update|delete|view|search|authenticate|authorize|login|register|logout|book|cancel|check|generate|send|receive|store|retrieve|display|show|hide|encrypt|decrypt|backup|restore|sync|integrate|connect|disconnect)\b',
            r'\b(?:shall|must|should|will|may)\s+(?:be|have|provide|allow|enable|support|facilitate|ensure|validate|process|handle|manage|create|update|delete|view|search|authenticate|authorize|login|register|logout|book|cancel|check|generate|send|receive|store|retrieve|display|show|hide|encrypt|decrypt|backup|restore|sync|integrate|connect|disconnect)\s+(?:data|information|access|functionality|capability|feature|service|interface|module|system|application|user|patient|doctor|admin|staff|record|history|profile|account|request|response|notification|alert|message|report|document|file|image|video|audio)\b',
            r'\b(?:patients|users|doctors|staff|admin|system|application)\s+(?:shall|must|should|will|may)\s+(?:be able to|be capable of|have the ability to|be permitted to|be authorized to|be allowed to)\s+(?:register|login|authenticate|access|view|edit|update|delete|create|manage|process|handle|generate|send|receive|store|retrieve|display|show|hide|book|cancel|check|validate|authorize|encrypt|decrypt|backup|restore|sync|integrate|connect|disconnect)\b',
        ]
        
        # Check if sentence matches professional patterns
        matches_professional = any(re.search(pattern, sentence, re.IGNORECASE) for pattern in professional_patterns)
        
        # Return True if it matches professional patterns or has modal + subject + action
        return matches_professional or (has_modal and has_subject and has_action)
    
    def identify_structure(self, text: str) -> List[Dict[str, Any]]:
        """Enhanced structure identification."""
        sections = []
        lines = text.split('\n')
        current_section = None
        section_text = []
        seq = 0
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            is_header = False
            
            # Check for section headers
            for pattern in self.SECTION_PATTERNS:
                if re.match(pattern, line_stripped, re.IGNORECASE):
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
            
            if not is_header:
                section_text.append(line_stripped)
        
        # Add the last section
        if current_section and section_text:
            sections.append({
                "title": current_section,
                "text": "\n".join(section_text).strip(),
                "sequence_order": seq,
            })
        
        return sections
    
    def parse_docx(self, content: str) -> Dict[str, Any]:
        """Enhanced DOCX parsing."""
        if not content:
            return {"error": "No content provided"}
        
        # Clean and extract text
        cleaned_text = self.sanitize_text(content)
        
        # Extract requirements with enhanced quality
        requirements = self.extract_requirements(cleaned_text)
        
        # Identify structure
        sections = self.identify_structure(cleaned_text)
        
        return {
            "text": cleaned_text,
            "word_count": len(cleaned_text.split()),
            "requirements": requirements,
            "sections": sections,
            "requirements_count": len(requirements)
        }
    
    def parse_pdf(self, content: str) -> Dict[str, Any]:
        """Enhanced PDF parsing."""
        return self.parse_docx(content)  # Same logic for now
    
    def parse_txt(self, content: str) -> Dict[str, Any]:
        """Enhanced TXT parsing."""
        return self.parse_docx(content)  # Same logic for now

# Factory function
def create_enhanced_parser():
    """Create enhanced parser instance."""
    return EnhancedDocumentParser()
