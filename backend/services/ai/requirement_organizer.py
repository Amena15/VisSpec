"""
Requirement Organizer Service.

Organizes, classifies, and enriches raw requirements with:
1. Module grouping (User Management, Authentication, etc.)
2. Semantic ID generation (FR-UM-01, NFR-SEC-01)
3. Text standardization to "The system shall..." format
4. Compound requirement splitting
5. Category classification (functional, non_functional, etc.)
6. Entity extraction (actors, modal verbs, vague terms)

This service is designed to run AFTER document upload (decoupled from
the HTTP upload request to prevent timeouts).
"""
import json
import re
from typing import Dict, List, Any, Optional

from core.logging import get_logger
from services.ai.llm_service import llm_service

logger = get_logger(__name__)


class RequirementOrganizer:
    """Organizes and enriches raw requirements into structured SRS format."""

    # Module keywords for rule-based grouping (fallback when LLM unavailable)
    MODULE_KEYWORDS = {
        "User Management": ["user", "account", "profile", "registration", "signup", "sign up", "register"],
        "Authentication": ["login", "logout", "signin", "sign in", "authenticate", "authentication", "credential", "password", "session", "token", "sso", "oauth", "mfa", "2fa", "biometric"],
        "Authorization & Access Control": ["role", "permission", "access", "authorize", "rbac", "acl", "privilege", "restrict", "grant", "deny"],
        "Dashboard & Reporting": ["dashboard", "report", "analytics", "metric", "kpi", "chart", "graph", "visualization", "overview", "summary", "statistic"],
        "Document Management": ["document", "file", "upload", "download", "attachment", "pdf", "docx", "storage", "folder", "repository"],
        "Notification & Communication": ["notification", "alert", "email", "sms", "message", "communication", "reminder", "broadcast", "push"],
        "Audit & Logging": ["audit", "log", "trail", "record", "history", "tracking", "monitor", "compliance"],
        "System Administration": ["admin", "administrator", "configuration", "setting", "system", "maintenance", "backup", "restore"],
        "Data Management": ["data", "database", "storage", "backup", "archive", "retention", "encryption", "privacy"],
        "Search & Filtering": ["search", "filter", "query", "sort", "find", "lookup", "index", "criteria"],
        "Workflow & Process": ["workflow", "approval", "review", "process", "stage", "step", "state", "transition"],
        "Integration & API": ["api", "integration", "interface", "webhook", "endpoint", "service", "third-party", "external system"],
        "Security & Compliance": ["security", "compliance", "regulation", "gdpr", "hipaa", "encryption", "secure", "vulnerability", "threat"],
        "Performance & Scalability": ["performance", "scalability", "latency", "throughput", "response time", "load", "concurrent", "capacity"],
    }

    # Category keywords for rule-based classification (fallback)
    CATEGORY_KEYWORDS = {
        "functional": ["shall", "must", "will", "function", "feature", "capability", "allow", "enable", "support", "provide"],
        "non_functional": ["performance", "scalability", "reliability", "availability", "usability", "maintainability", "security", "efficiency", "response time", "throughput"],
        "interface": ["interface", "api", "ui", "user interface", "screen", "form", "button", "menu", "dashboard", "display", "view"],
        "constraint": ["constraint", "limitation", "restrict", "comply", "regulation", "standard", "must not", "shall not", "only", "maximum", "minimum"],
        "data": ["data", "database", "storage", "field", "record", "schema", "table", "entity", "attribute", "json", "xml", "format"],
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
            # Use professional extraction prompt with smaller text for better results
            # First, try to extract only the main requirement sections, skip TOC/figures
            lines = full_text.split('\n')
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

        Steps:
        1. Try professional extraction first (if LLM available)
        2. Fallback to traditional pipeline if professional extraction fails
        3. Split compound requirements
        4. Standardize text format
        5. Group into modules
        6. Generate semantic IDs
        7. Classify by category (LLM or heuristic)
        8. Extract entities (actors, modal verbs, vague terms)
        """
        if not requirements:
            return []

        # Try professional extraction first if LLM is available
        if use_llm and llm_service.is_available:
            professional_reqs = self.extract_professional_requirements(full_text, use_llm)
            if professional_reqs:
                logger.info("Using professional extraction results")
                # Extract entities for the professional requirements
                professional_reqs = self._extract_entities(professional_reqs, use_llm)
                return professional_reqs
            else:
                logger.warning("Professional extraction failed, falling back to traditional pipeline")

        # Traditional pipeline as fallback
        # Step 1 & 2: Split compound and standardize
        atomic_reqs = []
        for req in requirements:
            split = self._split_compound_requirement(req)
            atomic_reqs.extend(split)

        # Step 3: Group into modules
        grouped = self._group_by_module(atomic_reqs, full_text, use_llm)

        # Step 4: Generate semantic IDs
        grouped = self._generate_semantic_ids(grouped)

        # Step 5: Classify by category
        grouped = self._classify_requirements(grouped, use_llm)

        # Step 6: Extract entities
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
        """Rule-based module grouping using keyword matching."""

        for req in requirements:
            text = req.get("original_text", "").lower()
            best_module = "General"
            best_score = 0

            for module, keywords in self.MODULE_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw.lower() in text)
                if score > best_score:
                    best_score = score
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

    def _generate_semantic_ids(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate hierarchical semantic IDs like FR-UM-01, NFR-SEC-01."""

        # Track counters per (category, module) pair
        counters = {}

        for req in requirements:
            module = req.get("module_name", "General")[:2].upper()
            category = req.get("category", "functional")

            # Map category to prefix
            prefix_map = {
                "functional": "FR",
                "non_functional": "NFR",
                "interface": "IR",
                "constraint": "CR",
                "data": "DR",
            }
            prefix = prefix_map.get(category, "REQ")

            # Get counter
            key = (prefix, module)
            counters[key] = counters.get(key, 0) + 1
            seq = counters[key]

            req["semantic_id"] = f"{prefix}-{module}-{seq:02d}"

        return requirements

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
                return requirements
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}, falling back to heuristic")

        # Fallback: heuristic classification
        for req in requirements:
            req["category"] = self._heuristic_classify(req.get("original_text", ""))
            req["category_confidence"] = 0.5

        return requirements

    def _heuristic_classify(self, text: str) -> str:
        """Rule-based classification fallback."""

        text_lower = text.lower()
        best_category = "functional"
        best_score = 0

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > best_score:
                best_score = score
                best_category = category

        return best_category

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
        """Safely parse JSON from LLM response."""
        try:
            # Remove markdown code blocks
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            return json.loads(text)
        except json.JSONDecodeError:
            return None


# Global instance
requirement_organizer = RequirementOrganizer()
