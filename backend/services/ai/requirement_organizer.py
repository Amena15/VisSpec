"""
Requirement Organizer Service.

Organizes, classifies, and enriches raw requirements with:
1. Module grouping (User Management, Authentication, etc.)
2. Semantic ID generation (FR-UM-01, NFR-SEC-01)
3. Text standardization to "The system shall..." format
4. Compound requirement splitting
5. Category classification (functional, non_functional, etc.)
6. Entity extraction (actors, modal verbs, vague terms)
7. Text cleaning (removes repeated words like willwill, shallshall)

This service is designed to run AFTER document upload (decoupled from
the HTTP upload request to prevent timeouts).
"""
import json
import re
import logging
from typing import Dict, List, Any, Optional

try:
    from backend.core.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

from backend.services.ai.llm_service import llm_service
from backend.services.ai.text_cleaner import TextCleaner



class RequirementOrganizer:
    """Organizes and enriches raw requirements into structured SRS format."""

    # Enhanced module keywords for rule-based grouping (fallback when LLM unavailable)
    MODULE_KEYWORDS = {
        "User Management": [
            "user", "account", "profile", "registration", "signup", "sign up", "register", 
            "create account", "user profile", "user details", "personal information", 
            "user preferences", "user settings", "manage account", "update profile"
        ],
        "Authentication": [
            "login", "logout", "signin", "sign in", "authenticate", "authentication", 
            "credential", "password", "session", "token", "sso", "oauth", "mfa", "2fa", 
            "biometric", "two-factor", "multi-factor", "single sign-on", "identity", 
            "verify identity", "user verification", "access credentials"
        ],
        "Authorization & Access Control": [
            "role", "permission", "access", "authorize", "rbac", "acl", "privilege", 
            "restrict", "grant", "deny", "access control", "user role", "admin role", 
            "user permission", "security level", "access rights", "privilege management"
        ],
        "Document Management": [
            "document", "file", "upload", "download", "attachment", "pdf", "docx", 
            "storage", "folder", "repository", "file management", "document storage", 
            "file sharing", "version control", "document library", "file system"
        ],
        "Dashboard & Reporting": [
            "dashboard", "report", "analytics", "metric", "kpi", "chart", "graph", 
            "visualization", "overview", "summary", "statistic", "data visualization", 
            "business intelligence", "reporting tool", "analytics dashboard", 
            "performance metrics", "data analysis"
        ],
        "Notification & Communication": [
            "notification", "alert", "email", "sms", "message", "communication", 
            "reminder", "broadcast", "push", "alert system", "messaging", 
            "email notification", "sms alert", "push notification", "communication system"
        ],
        "Audit & Logging": [
            "audit", "log", "trail", "record", "history", "tracking", "monitor", 
            "compliance", "audit trail", "system log", "activity log", "audit record", 
            "compliance monitoring", "audit system", "logging system"
        ],
        "System Administration": [
            "admin", "administrator", "configuration", "setting", "system", 
            "maintenance", "backup", "restore", "system configuration", "admin panel", 
            "system settings", "maintenance mode", "system backup", "admin tools"
        ],
        "Data Management": [
            "data", "database", "storage", "backup", "archive", "retention", 
            "encryption", "privacy", "data protection", "database management", 
            "data storage", "data backup", "data security", "data privacy"
        ],
        "Search & Filtering": [
            "search", "filter", "query", "sort", "find", "lookup", "index", 
            "criteria", "search function", "filter results", "data search", 
            "advanced search", "search algorithm", "filter options"
        ],
        "Workflow & Process": [
            "workflow", "approval", "review", "process", "stage", "step", 
            "state", "transition", "business process", "workflow management", 
            "approval process", "process automation", "workflow state"
        ],
        "Integration & API": [
            "api", "integration", "interface", "webhook", "endpoint", "service", 
            "third-party", "external system", "api integration", "web service", 
            "system integration", "api endpoint", "external api"
        ],
        "Security & Compliance": [
            "security", "compliance", "regulation", "gdpr", "hipaa", "encryption", 
            "secure", "vulnerability", "threat", "security policy", "data security", 
            "cybersecurity", "threat detection", "security compliance"
        ],
        "Performance & Scalability": [
            "performance", "scalability", "latency", "throughput", "response time", 
            "load", "concurrent", "capacity", "system performance", "scalability", 
            "performance optimization", "load balancing", "capacity planning"
        ],
        "User Interface & Experience": [
            "interface", "ui", "user interface", "screen", "form", "button", 
            "menu", "display", "view", "user experience", "ux design", 
            "interface design", "user interaction", "screen layout"
        ],
        "Business Logic": [
            "business rule", "logic", "calculation", "validation", "business process", 
            "algorithm", "business logic", "rule engine", "validation rule", 
            "business calculation", "process rule"
        ]
    }

    # Enhanced category keywords for rule-based classification (fallback)
    CATEGORY_KEYWORDS = {
        "functional": [
            "shall", "must", "will", "function", "feature", "capability", "allow", "enable", 
            "support", "provide", "perform", "execute", "process", "handle", "manage", 
            "create", "update", "delete", "read", "view", "edit", "add", "remove", "generate", 
            "calculate", "validate", "verify", "approve", "reject", "submit", "save", "store", 
            "retrieve", "display", "show", "hide", "send", "receive", "transmit", "transfer"
        ],
        "non_functional": [
            "performance", "scalability", "reliability", "availability", "usability", "maintainability", 
            "security", "efficiency", "response time", "throughput", "latency", "load", "capacity", 
            "concurrent", "simultaneous", "multi-user", "real-time", "batch", "scheduled", "automatic", 
            "manual", "quality", "accuracy", "precision", "consistency", "integrity", "robustness", 
            "flexibility", "portability", "interoperability", "compatibility", "testability"
        ],
        "interface": [
            "interface", "api", "ui", "user interface", "screen", "form", "button", "menu", 
            "dashboard", "display", "view", "page", "window", "dialog", "modal", "popup", 
            "navigation", "search bar", "input field", "dropdown", "checkbox", "radio button", 
            "slider", "tab", "breadcrumb", "link", "hyperlink", "tooltip", "icon", "image"
        ],
        "constraint": [
            "constraint", "limitation", "restrict", "comply", "regulation", "standard", 
            "must not", "shall not", "only", "maximum", "minimum", "shall", "should", "must", 
            "will", "requirement", "specification", "policy", "rule", "guideline", "procedure", 
            "protocol", "format", "template", "schema", "validation", "verification", "audit"
        ],
        "data": [
            "data", "database", "storage", "field", "record", "schema", "table", "entity", 
            "attribute", "json", "xml", "format", "file", "document", "content", "information", 
            "metadata", "log", "backup", "archive", "export", "import", "migration", "synchronization", 
            "replication", "version", "history", "audit trail", "index", "key", "relationship"
        ],
        "security": [
            "security", "authentication", "authorization", "access", "permission", "role", 
            "privilege", "login", "password", "token", "session", "encryption", "decryption", 
            "secure", "protect", "prevent", "detect", "monitor", "audit", "compliance", "privacy", 
            "confidential", "sensitive", "vulnerability", "threat", "risk", "attack", "breach"
        ],
        "integration": [
            "integration", "api", "web service", "endpoint", "interface", "third-party", 
            "external", "system", "application", "service", "connect", "communicate", 
            "exchange", "synchronize", "import", "export", "feed", "webhook", "callback", 
            "notification", "event", "message", "queue", "protocol", "standard"
        ]
    }

    # Modal verbs to detect
    MODAL_VERBS = ["shall", "should", "must", "will", "may", "might", "could", "would", "can"]

    # Vague terms to flag
    VAGUE_TERMS = [
        "appropriate", "appropriately", "reasonable", "reasonably", "timely", "adequate", "adequately",
        "suitable", "user-friendly", "efficient", "fast", "quick", "easy", "good", "bad", "large",
        "small", "many", "few", "as needed", "etc.", "and so on", "depending on", "if applicable",
        "usually", "often", "typically", "generally", "maybe", "perhaps", "possibly", "sometimes",
        "soon", "later", "eventually", "when possible", "tbd", "to be determined", "to be decided",
    ]

    def extract_professional_requirements(
        self,
        full_text: str,
        use_llm: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Extract clean, atomic requirements directly from document text using professional prompt.
        
        This method uses the new engineering-grade prompt that:
        1. Actively filters out document noise (TOC, figures, tables, headers)
        2. Extracts only atomic, testable requirements
        3. Standardizes text using RFC 2119 terminology
        4. Generates semantic IDs and categorizes automatically
        """
        if not use_llm or not llm_service.is_available:
            logger.warning("LLM not available, cannot extract professional requirements")
            return []

        try:
            # Step 0: Clean the full text first to remove repeated words
            cleaned_full_text = TextCleaner.clean_requirement_text(full_text)
            
            # Use professional extraction prompt with smaller text for better results
            # First, try to extract only the main requirement sections, skip TOC/figures
            lines = cleaned_full_text.split('\n')
            requirement_lines = []
            skip_sections = ['Table ', 'Figure ', 'Appendix', 'Contents', 'Overview', 'Summary']
            
            for line in lines:
                line = line.strip()
                # Skip obvious noise lines
                if any(skip_word in line for skip_word in skip_sections):
                    continue
                # Skip empty lines
                if not line or len(line) < 10:
                    continue
                requirement_lines.append(line)
            
            # Use only requirement lines for extraction (more focused)
            focused_text = '\n'.join(requirement_lines[:20])  # Limit to first 20 lines for 30-second timeout
            
            try:
                result = llm_service.extract_requirements(focused_text)
                
                if isinstance(result, dict):
                    # Single requirement returned, convert to list
                    extracted_reqs = [result] if "requirements" in result else []
                elif isinstance(result, list):
                    # Multiple requirements returned (expected format)
                    extracted_reqs = result
                else:
                    # Unexpected format, log and return empty
                    logger.error(f"Unexpected LLM response format: {type(result)} - {str(result)[:200]}")
                    extracted_reqs = []
                
                logger.info(f"Extracted {len(extracted_reqs)} requirements")
                
                # If no requirements extracted, skip to fallback immediately
                if not extracted_reqs:
                    logger.warning("No requirements from LLM, using fallback")
                    raise Exception("No requirements extracted from LLM")
                
            except Exception as e:
                logger.error(f"Professional requirements extraction failed: {e}")
                # Return empty list on error to prevent frontend issues
                return []

            # Ensure all required fields are present
            processed_reqs = []
            for req in extracted_reqs:
                # Debug: Log the type and content of req
                logger.debug(f"Processing req: {type(req)} - {str(req)[:100]}")
                
                # Handle both dict and string types safely
                if isinstance(req, dict):
                    processed_req = {
                        "original_text": req.get("original_text", ""),
                        "current_text": req.get("original_text", ""),  # Initially same as original
                        "category": req.get("category", "functional"),
                        "category_confidence": 0.8,  # High confidence from LLM extraction
                        "semantic_id": req.get("semantic_id", ""),
                        "module_name": req.get("module_name", "General"),
                        "actors_json": json.dumps(req.get("actors", [])),
                        "modal_verbs_json": json.dumps([]),  # Will be extracted separately
                        "vague_terms_json": json.dumps([]),  # Will be extracted separately
                    }
                else:
                    # Handle case where req is already a string
                    logger.debug(f"Processing string req: {req[:100]}")
                    processed_req = {
                        "original_text": req,
                        "current_text": req,
                        "category": "functional",
                        "category_confidence": 0.7,
                        "semantic_id": f"FR-{len(processed_reqs)+1:02d}",
                        "module_name": "General",
                        "actors_json": json.dumps([]),
                        "modal_verbs_json": json.dumps([]),
                        "vague_terms_json": json.dumps([])
                    }
                processed_reqs.append(processed_req)

            return processed_reqs

        except Exception as e:
            logger.error(f"Professional requirements extraction failed: {e}")
            return []

    def organize_and_enrich(
        self,
        requirements: List[Dict[str, Any]],
        full_text: str,
        use_llm: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Main entry point: takes raw requirements and returns fully enriched ones.
        """
        if not requirements:
            logger.warning("No requirements provided for enrichment")
            return []

        # Step 0: Clean text first (remove repeated words like willwill, shallshall)
        cleaned_requirements = TextCleaner.clean_requirements_batch(requirements)
        
        # Step 1 & 2: Split compound and standardize
        atomic_reqs = []
        for req in cleaned_requirements:
            split = self._split_compound_requirement(req)
            atomic_reqs.extend(split)

        # Step 3: Group into modules (Safely uses LLM while keeping req_id)
        grouped = self._group_by_module(atomic_reqs, full_text, use_llm)

        # Step 4: Classify by category (Safely uses LLM while keeping req_id)
        grouped = self._classify_requirements(grouped, use_llm)

        # Step 5: Generate semantic IDs
        grouped = self._generate_semantic_ids(grouped)

        # Step 6: Extract entities (Safely uses LLM while keeping req_id)
        grouped = self._extract_entities(grouped, use_llm)

        return grouped

    def _split_compound_requirement(self, req: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a compound requirement into atomic ones.
        Enhanced detection for better atomicity.
        """
        text = req.get("original_text", "")
        if not text:
            return [req]

        # First, clean up the text
        text = re.sub(r'\s+', ' ', text).strip()

        # Enhanced pattern for detecting multiple modal verbs in one sentence
        # This catches requirements like "The system shall do X and must do Y"
        multi_modal_pattern = r"(?:^|\.\s*)(.+?)(?:\s+(?:shall|must|should|will|may)\s+)(.+?)(?:\.\s*$|$)"
        multi_modal_matches = re.findall(multi_modal_pattern, text, re.IGNORECASE)

        if multi_modal_matches:
            result = []
            # Split by multiple modal verbs
            parts = re.split(r'\s+(?:shall|must|should|will|may)\s+', text, flags=re.IGNORECASE)
            modal_verbs = re.findall(r'(?:shall|must|should|will|may)', text, re.IGNORECASE)
            
            for i, part in enumerate(parts):
                if part.strip() and i < len(modal_verbs) + 1:
                    modal = modal_verbs[i-1] if i > 0 else modal_verbs[0]
                    clean_part = f"The system {modal} {part.strip().rstrip('.')}"
                    if len(clean_part.split()) > 5:  # Ensure meaningful content
                        new_req = dict(req)
                        new_req["original_text"] = clean_part
                        new_req["word_count"] = len(clean_part.split())
                        new_req["sequence_order"] = req.get("sequence_order", 0) + i
                        result.append(new_req)
            
            if result:
                return result

        # Detect "and" / "or" conjunctions with modal verbs
        conjunction_pattern = r"(.+?)(?:\s+(?:and|or)\s+)(.+?)(?=\.\s*$|$)"
        conjunction_matches = re.findall(conjunction_pattern, text, re.IGNORECASE)

        if conjunction_matches and len(conjunction_matches[0]) == 2:
            result = []
            parts = conjunction_matches[0]
            
            # Check if both parts have modal verbs or can be standalone requirements
            for i, part in enumerate(parts):
                part = part.strip()
                # Add modal verb if missing for consistency
                if not any(modal in part.lower() for modal in ['shall', 'must', 'should', 'will']):
                    # Find modal verb from original text or add 'shall'
                    original_modals = re.findall(r'(?:shall|must|should|will)', text, re.IGNORECASE)
                    modal = original_modals[0] if original_modals else 'shall'
                    part = f"The system {modal} {part}"
                
                if len(part.split()) > 5:  # Ensure meaningful content
                    new_req = dict(req)
                    new_req["original_text"] = part.rstrip('.') + '.'
                    new_req["word_count"] = len(part.split())
                    new_req["sequence_order"] = req.get("sequence_order", 0) + i
                    result.append(new_req)
            
            if result:
                return result

        # Detect semicolon-separated requirements
        if ';' in text:
            parts = [p.strip() for p in text.split(';') if p.strip()]
            if len(parts) > 1:
                result = []
                for i, part in enumerate(parts):
                    if len(part.split()) > 5:
                        # Ensure it has a modal verb
                        if not any(modal in part.lower() for modal in ['shall', 'must', 'should', 'will']):
                            original_modals = re.findall(r'(?:shall|must|should|will)', text, re.IGNORECASE)
                            modal = original_modals[0] if original_modals else 'shall'
                            part = f"The system {modal} {part}"
                        
                        new_req = dict(req)
                        new_req["original_text"] = part.rstrip('.') + '.'
                        new_req["word_count"] = len(part.split())
                        new_req["sequence_order"] = req.get("sequence_order", 0) + i
                        result.append(new_req)
                
                if result:
                    return result

        # No splitting needed - return original
        return [req]

    def _standardize_text(self, text: str) -> str:
        """
        Standardize requirement text to "The system shall..." format.
        Does not change core business logic.
        """
        text = text.strip()

        # If already starts with "The system", keep it
        if re.match(r"^\s*The\s+system\s+(?:shall|should|must|will|may)\b", text, re.IGNORECASE):
            return text

        # Detect sentences with modal verbs and restructure
        modal_match = re.search(r"\b(?:shall|should|must|will|may)\b", text, re.IGNORECASE)
        if modal_match:
            # Extract the part after the modal verb
            before_modal = text[:modal_match.start()].strip()
            after_modal = text[modal_match.start():].strip()

            # If starts with a subject-like word, keep it
            subjects = ["the system", "the application", "the software", "it", "users", "administrators"]
            if any(before_modal.lower().startswith(s) for s in subjects):
                return text

            # Otherwise, prepend "The system"
            return f"The system {after_modal.lower()}"

        # If no modal verb, assume it's a functional requirement and add "shall"
        return f"The system shall {text[0].lower()}{text[1:]}"

    def _group_by_module(
        self,
        requirements: List[Dict[str, Any]],
        full_text: str,
        use_llm: bool,
    ) -> List[Dict[str, Any]]:
        """Group requirements into logical modules."""

        # Try LLM-based grouping first
        if use_llm and llm_service.is_available:
            try:
                return self._group_by_module_llm(requirements, full_text)
            except Exception as e:
                logger.warning(f"LLM module grouping failed: {e}, falling back to heuristic")

        # Fallback: rule-based grouping
        return self._group_by_module_heuristic(requirements)

    def _group_by_module_heuristic(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhanced rule-based module grouping using weighted keyword matching."""

        for req in requirements:
            text = req.get("original_text", "").lower()
            best_module = "General"
            best_score = 0

            # Module importance weights - some modules are more specific
            module_weights = {
                "Authentication": 2.5,
                "Document Management": 2.3,
                "Security & Compliance": 2.4,
                "User Management": 2.2,
                "Authorization & Access Control": 2.1,
                "Dashboard & Reporting": 1.9,
                "Integration & API": 2.0,
                "Audit & Logging": 2.0,
                "Performance & Scalability": 1.8,
                "Data Management": 1.7,
                "Notification & Communication": 1.6,
                "Search & Filtering": 1.5,
                "Workflow & Process": 1.4,
                "System Administration": 1.3,
                "User Interface & Experience": 1.2,
                "Business Logic": 1.1,
                "General": 0.5,
            }

            for module, keywords in self.MODULE_KEYWORDS.items():
                score = 0
                text_words = text.split()
                
                # Count keyword matches with different weights
                for kw in keywords:
                    kw_lower = kw.lower()
                    
                    # Exact phrase match (higher score)
                    if ' ' in kw and kw_lower in text:
                        score += 3
                    # Single word match
                    elif kw_lower in text:
                        score += 1
                
                # Apply module weight
                weighted_score = score * module_weights.get(module, 1.0)
                
                # Normalize by text length
                normalized_score = weighted_score / max(len(text_words), 1)
                
                if normalized_score > best_score:
                    best_score = normalized_score
                    best_module = module

            req["module_name"] = best_module

        return requirements

    def _group_by_module_llm(
        self,
        requirements: List[Dict[str, Any]],
        full_text: str,
    ) -> List[Dict[str, Any]]:
        """LLM-based module grouping."""

        prompt = f"""You are a senior requirements analyst. Group the following requirements into logical system modules.

Rules:
- Create 3-8 meaningful module names (e.g., "User Management", "Authentication", "Dashboard & Reporting")
- Each requirement belongs to exactly one module
- Use the full document context to understand the domain

Return JSON only:
{{
  "modules": [
    {{
      "module_name": "Module Name",
      "requirements": ["requirement text 1", "requirement text 2"]
    }}
  ]
}}

Document context (first 2000 chars):
{full_text[:2000]}

Requirements to group:
{"\n".join(f"- {r['original_text'][:200]}" for r in requirements)}
"""

        response = llm_service.call_with_retry(prompt, max_tokens=4096)
        if not response:
            raise ValueError("LLM returned empty response")

        parsed = self._safe_parse_json(response)
        if not parsed or "modules" not in parsed:
            raise ValueError("Invalid LLM response format")

        # Map requirements back to their modules
        module_map = {}
        for mod in parsed["modules"]:
            mod_name = mod["module_name"]
            for req_text in mod.get("requirements", []):
                module_map[req_text.strip().lower()[:150]] = mod_name

        # Assign modules to requirements
        for req in requirements:
            text = req.get("original_text", "").strip().lower()[:150]
            req["module_name"] = module_map.get(text, "General")

        return requirements

    @staticmethod
    def _abbreviate_module_name(module_name: str) -> str:
        """Build a short code from a module title (e.g. 'Laboratory Management' -> 'LM')."""
        if not module_name or not str(module_name).strip():
            return "GEN"
        clean = re.sub(r"[^a-zA-Z0-9\s]", "", str(module_name)).strip()
        if not clean:
            return "GEN"
        parts = clean.split()
        if len(parts) >= 2:
            initials = "".join(p[0].upper() for p in parts[:5] if p)
            return initials[:4] if initials else "GEN"
        return clean[:4].upper()

    def _generate_semantic_ids(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhanced semantic ID generation with meaningful module codes."""

        # Track counters per (category, module) pair
        counters = {}

        # Module code mapping for more meaningful IDs
        module_codes = {
            "User Management": "UM",
            "Authentication": "AUTH",
            "Authorization & Access Control": "AC",
            "Document Management": "DM",
            "Dashboard & Reporting": "DR",
            "Notification & Communication": "NC",
            "Audit & Logging": "AL",
            "System Administration": "SA",
            "Data Management": "DT",
            "Search & Filtering": "SF",
            "Workflow & Process": "WF",
            "Integration & API": "API",
            "Security & Compliance": "SEC",
            "Performance & Scalability": "PERF",
            "User Interface & Experience": "UI",
            "Business Logic": "BL",
            "General": "GEN",
            "Laboratory Management": "LAB",
            "Doctor Management": "DRM",
            "Patient Management": "PAT",
            "Chemist Management": "CHM",
        }

        # Category to prefix mapping
        prefix_map = {
            "functional": "FR",
            "non_functional": "NFR",
            "interface": "UIR",
            "constraint": "CR",
            "data": "DR",
            "security": "SEC",
            "integration": "INT",
        }

        for req in requirements:
            module_name = req.get("module_name", "General")
            category = req.get("category", "functional")

            # Get module code (explicit map, else derive from module title)
            module_code = module_codes.get(module_name)
            if not module_code:
                module_code = self._abbreviate_module_name(module_name)
            
            # Get category prefix
            prefix = prefix_map.get(category, "REQ")

            # Get counter for this combination
            key = (prefix, module_code)
            counters[key] = counters.get(key, 0) + 1
            seq = counters[key]

            req["semantic_id"] = f"{prefix}-{module_code}-{seq:02d}"

        return requirements

    def _calculate_requirement_quality(self, text: str) -> Dict[str, Any]:
        """Calculate quality metrics for a requirement."""
        
        quality_score = 100.0
        issues = []
        
        # Check for modal verbs (should have at least one)
        modal_verbs = ["shall", "must", "should", "will", "may"]
        has_modal = any(modal in text.lower() for modal in modal_verbs)
        if not has_modal:
            quality_score -= 20
            issues.append("Missing modal verb (shall/must/should/will)")
        
        # Check for vague terms
        vague_terms_found = [term for term in self.VAGUE_TERMS if term in text.lower()]
        if vague_terms_found:
            quality_score -= len(vague_terms_found) * 5
            issues.append(f"Contains vague terms: {', '.join(vague_terms_found[:3])}")
        
        # Check length (too short or too long)
        word_count = len(text.split())
        if word_count < 5:
            quality_score -= 15
            issues.append("Too short (may be incomplete)")
        elif word_count > 50:
            quality_score -= 10
            issues.append("Too long (may be compound requirement)")
        
        # Check for actors (should have at least one)
        actors = self._extract_actors_heuristic(text)
        if not actors:
            quality_score -= 10
            issues.append("No clear actor identified")
        
        # Check for measurable criteria
        measurable_terms = ["seconds", "minutes", "hours", "days", "percent", "%", "number", "count", "limit", "maximum", "minimum"]
        has_measurable = any(term in text.lower() for term in measurable_terms)
        nfr_hint = any(
            x in text.lower()
            for x in (
                "performance", "availability", "scalability", "latency", "throughput",
                "response time", "uptime", "reliability", "maintainability", "backup",
            )
        )
        if not has_measurable and nfr_hint:
            quality_score -= 15
            issues.append("Non-functional requirement lacks measurable criteria")
        
        return {
            "quality_score": max(0, quality_score),
            "issues": issues,
            "word_count": word_count,
            "has_modal": has_modal,
            "actors": actors,
            "vague_terms": vague_terms_found
        }

    def _classify_requirements(
        self,
        requirements: List[Dict[str, Any]],
        use_llm: bool,
    ) -> List[Dict[str, Any]]:
        """Classify each requirement by category."""

        texts = [r.get("original_text", "") for r in requirements]

        # Try LLM classification first
        if use_llm and llm_service.is_available and texts:
            try:
                combined_text = "\n".join(f"- {t}" for t in texts)
                result = llm_service.classify_requirements(combined_text)

                classifications = result.get("classifications", [])
                for i, req in enumerate(requirements):
                    if i < len(classifications):
                        req["category"] = classifications[i].get("category", "functional")
                        req["category_confidence"] = classifications[i].get("confidence", 0.5)
                    else:
                        # Fallback for missing classifications
                        req["category"] = self._heuristic_classify(req.get("original_text", ""))
                        req["category_confidence"] = 0.3
                # LLM often defaults everything to functional; reconcile with keyword heuristics
                for i, req in enumerate(requirements):
                    if i >= len(classifications):
                        continue
                    heur = self._heuristic_classify(req.get("original_text", ""))
                    llm_cat = (classifications[i].get("category") or "functional").lower()
                    if llm_cat == "functional" and heur != "functional":
                        req["category"] = heur
                        req["category_confidence"] = max(
                            float(classifications[i].get("confidence") or 0.5),
                            0.72,
                        )
                return requirements
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}, falling back to heuristic")

        # Fallback: heuristic classification
        for req in requirements:
            req["category"] = self._heuristic_classify(req.get("original_text", ""))
            req["category_confidence"] = 0.5

        return requirements

    def _heuristic_classify(self, text: str) -> str:
        """
        Rule-based category from requirement text.
        Non-functional / security / data cues are checked before generic functional
        (almost all SRS lines contain shall/must — those must not force 'functional').
        """
        text_lower = text.lower()

        priority = [
            (
                "non_functional",
                [
                    "non-functional", "non functional", "nfr-", "nfr ",
                    "performance", "response time", "throughput", "latency",
                    "availability", "uptime", "99.99", "99.999", "24/7", "mean time",
                    "mtbf", "mttr", "recoverability", "disaster recovery",
                    "scalability", "scalable", "concurrent users", "load balancing",
                    "maintainability", "maintainable", "portability", "usability",
                    "reliability", "benchmark", "capacity planning", "resource usage",
                    "memory footprint", "cpu usage", "timeout", "sla", "service level",
                    "backup", "restore", "archiv", "retention policy",
                ],
            ),
            (
                "security",
                [
                    "encrypt", "encryption", "tls", "ssl", "https",
                    "authentication", "authorization", "password policy",
                    "confidential", "vulnerability", "breach", "rbac",
                    "access control", "audit trail", "gdpr", "hipaa",
                ],
            ),
            (
                "interface",
                [
                    "user interface", "gui", "screen layout", "ux ",
                    " ui ", "dashboard", "form field", "navigation menu",
                ],
            ),
            (
                "integration",
                [
                    "third-party", "third party", "external system", "webhook",
                    "api integration", "interoperat", "hl7", "fhir",
                ],
            ),
            (
                "data",
                [
                    "database", "schema", "data model", "persist", "sql ",
                    "json schema", "data retention", "data migration",
                ],
            ),
            (
                "constraint",
                [
                    "regulation", "compliance", "must comply", "legal requirement",
                    "standard iso", "constraint:", "restriction:",
                ],
            ),
        ]

        for cat, phrases in priority:
            if any(p in text_lower for p in phrases):
                return cat

        scores: Dict[str, float] = {c: 0.0 for c in self.CATEGORY_KEYWORDS}
        weak_modal_tokens = {"shall", "must", "will", "should", "may", "might", "could", "would", "can"}

        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                kl = kw.lower()
                if len(kl) < 3 or kl not in text_lower:
                    continue
                weight = 2.5 if " " in kl else 1.0
                if cat == "functional" and kl in weak_modal_tokens:
                    weight = 0.12
                scores[cat] += weight

        best_cat, best_score = max(scores.items(), key=lambda kv: kv[1])
        if best_score >= 0.35:
            return best_cat
        return "functional"

    def _extract_entities(
        self,
        requirements: List[Dict[str, Any]],
        use_llm: bool,
    ) -> List[Dict[str, Any]]:
        """Extract actors, modal verbs, and vague terms for each requirement."""

        texts = [r.get("original_text", "") for r in requirements]

        # Try LLM entity extraction first
        if use_llm and llm_service.is_available and texts:
            try:
                combined_text = "\n".join(f"- {t}" for t in texts)
                result = llm_service.extract_entities(combined_text)

                # LLM returns combined results - we need to map per requirement
                # For now, use the combined results for all requirements
                # (In production, you'd call per requirement or use a smarter mapping)
                all_actors = result.get("entities", [])
                all_modal_verbs = result.get("modal_verbs", [])
                all_vague_terms = result.get("vague_terms", [])

                for req in requirements:
                    text = req.get("original_text", "").lower()

                    # Filter actors that appear in this requirement
                    req_actors = [
                        e["text"] for e in all_actors
                        if e.get("label") == "ACTOR" and e.get("text", "").lower() in text
                    ]

                    # Filter modal verbs
                    req_modals = [mv for mv in all_modal_verbs if mv.lower() in text]

                    # Filter vague terms
                    req_vague = [vt for vt in all_vague_terms if vt.lower() in text]

                    req["actors"] = list(set(req_actors))
                    req["modal_verbs"] = list(set(req_modals))
                    req["vague_terms"] = list(set(req_vague))

                return requirements
            except Exception as e:
                logger.warning(f"LLM entity extraction failed: {e}, falling back to heuristic")

        # Fallback: heuristic extraction per requirement
        for req in requirements:
            text = req.get("original_text", "")
            req["actors"] = self._extract_actors_heuristic(text)
            req["modal_verbs"] = self._extract_modal_verbs(text)
            req["vague_terms"] = self._extract_vague_terms(text)

        return requirements

    def _extract_actors_heuristic(self, text: str) -> List[str]:
        """Extract actor names using keyword matching."""
        text_lower = text.lower()
        actor_keywords = [
            "user", "admin", "administrator", "manager", "operator", "staff",
            "employee", "member", "customer", "client", "patient", "doctor",
            "nurse", "teacher", "student", "supervisor", "analyst", "developer",
            "system", "application", "software", "api", "database", "server",
        ]
        found = []
        for actor in actor_keywords:
            if actor in text_lower:
                found.append(actor.title())
        return list(set(found))

    def _extract_modal_verbs(self, text: str) -> List[str]:
        """Extract modal verbs from text."""
        text_lower = text.lower()
        found = [mv for mv in self.MODAL_VERBS if mv in text_lower]
        return list(set(found))

    def _extract_vague_terms(self, text: str) -> List[str]:
        """Extract vague terms from text."""
        text_lower = text.lower()
        found = [vt for vt in self.VAGUE_TERMS if vt.lower() in text_lower]
        return list(set(found))

    @staticmethod
    def _safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
        """Safely parse JSON from LLM response, ignoring conversational filler."""
        try:
            text = text.strip()
            
            # Use regex to extract everything from the first '{' or '[' to the last '}' or ']'
            import re
            match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
            
            if match:
                clean_json = match.group(0)
                return json.loads(clean_json)
            
            # Fallback if no brackets are found
            return json.loads(text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e} | Raw text: {text[:200]}")
            return None


# Global instance
requirement_organizer = RequirementOrganizer()
