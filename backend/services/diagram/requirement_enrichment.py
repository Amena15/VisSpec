"""
Requirement Enrichment Service for IEEE-Compliant Diagram Generation.

This service enriches requirements with metadata needed for accurate diagram generation:
- actors_json: list of actors explicitly mentioned
- modal_verbs_json: e.g., ["shall", "must"]
- category: functional, non_functional, interface, constraint, data, security
- semantic_id: unique ID (e.g., FR-LOG-01, NFR-SEC-02)
- module_name: logical grouping (e.g., "User Management", "Security & Compliance")

Uses LLM-first approach with rule-based fallback for accuracy.
"""

import json
import re
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.services.ai.llm_service import GroqLLMService
from backend.core.logging import get_logger

logger = get_logger(__name__)


class RequirementEnrichmentService:
    """Enriches requirements with metadata for accurate diagram generation."""
    
    def __init__(self):
        self.llm_client = GroqLLMService()
        self.cache = {}  # Simple in-memory cache for enrichment results
        
    def enrich_requirement(self, requirement_text: str, req_identifier: str = None) -> Dict[str, Any]:
        """
        Enrich a single requirement with metadata.
        
        Args:
            requirement_text: The requirement text to enrich
            req_identifier: Optional requirement identifier
            
        Returns:
            Dictionary with enrichment data
        """
        # Check cache first
        text_hash = hashlib.md5(requirement_text.encode()).hexdigest()
        if text_hash in self.cache:
            logger.info(f"Cache hit for {req_identifier}")
            return self.cache[text_hash]
        
        try:
            # Try LLM-first approach with retry logic
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    llm_result = self._enrich_with_llm(requirement_text)
                    if llm_result and self._validate_enrichment(llm_result):
                        logger.info(f"LLM enrichment successful for {req_identifier}")
                        self.cache[text_hash] = llm_result
                        return llm_result
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit for {req_identifier}, retry {attempt + 1}/{max_retries}")
                        import time
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    else:
                        raise
            
            # If all retries fail, use rule-based fallback
            logger.warning(f"LLM enrichment failed for {req_identifier} after {max_retries} retries, using rule-based fallback")
            result = self._enrich_rule_based(requirement_text, req_identifier)
            self.cache[text_hash] = result
            return result
            
        except Exception as e:
            logger.error(f"LLM enrichment error for {req_identifier}: {e}")
            # Always return rule-based fallback on error
            result = self._enrich_rule_based(requirement_text, req_identifier)
            self.cache[text_hash] = result
            return result
    
    def _enrich_with_llm(self, requirement_text: str) -> Optional[Dict[str, Any]]:
        """Use LLM to extract enrichment data."""
        try:
            prompt = f"""
Analyze the following requirement and extract structured metadata:

Requirement: "{requirement_text}"

Extract and return ONLY a JSON object with these exact fields:
{{
    "actors": ["list of actors mentioned"],
    "modal_verbs": ["shall", "must", "should", "will", "may"],
    "category": "functional|non_functional|interface|constraint|data|security",
    "semantic_id": "generate a semantic ID like FR-LOG-01",
    "module_name": "logical module name"
}}

Rules:
- Actors: Only extract entities that perform actions or receive actions
- Category: Determine based on requirement type
- Semantic ID: Use pattern: [FR/NFR]-[MODULE]-[NUMBER]
- Module name: Group related functionality
- Return ONLY valid JSON, no additional text
"""
            
            response = self.llm_client._make_request(prompt)
            
            # Parse JSON response
            if response:
                # Extract JSON from response if it contains extra text
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    response = json_match.group(0)
                
                result = json.loads(response)
                
                # Transform to expected format
                return {
                    "actors_json": json.dumps(result.get("actors", [])),
                    "modal_verbs_json": json.dumps(result.get("modal_verbs", [])),
                    "category": result.get("category", "functional"),
                    "semantic_id": result.get("semantic_id"),
                    "module_name": result.get("module_name", "General")
                }
            
            return None
            
        except Exception as e:
            logger.error(f"LLM enrichment error: {e}")
            return None
    
    def _enrich_rule_based(self, requirement_text: str, req_identifier: str = None) -> Dict[str, Any]:
        """Rule-based fallback for requirement enrichment."""
        # Extract actors using common patterns
        actors = self._extract_actors_rule_based(requirement_text)
        
        # Extract modal verbs
        modal_verbs = self._extract_modal_verbs(requirement_text)
        
        # Determine category
        category = self._determine_category(requirement_text)
        
        # Generate semantic ID
        semantic_id = self._generate_semantic_id(category, req_identifier)
        
        # Determine module name
        module_name = self._determine_module_name(requirement_text)
        
        return {
            "actors_json": json.dumps(actors),
            "modal_verbs_json": json.dumps(modal_verbs),
            "category": category,
            "semantic_id": semantic_id,
            "module_name": module_name
        }
    
    def _extract_actors_rule_based(self, text: str) -> List[str]:
        """Extract actors using rule-based patterns."""
        actors = []
        text_lower = text.lower()
        
        # Comprehensive actor patterns - more specific first
        actor_patterns = [
            # Specific roles
            r'\b(admin|administrator|administ)\b',
            r'\b(doctor|physician|medical staff)\b',
            r'\b(patient|patients)\b',
            r'\b(hospital|clinic|medical center)\b',
            r'\b(government|government of india|authority)\b',
            r'\b(elderly|elderly people|senior citizen)\b',
            r'\b(database|server|system)\b',
            r'\b(external api|external service|third party)\b',
            r'\b(management|manager)\b',
            r'\b(staff|employee)\b',
            r'\b(customer|client|user)\b',
            r'\b(guest|visitor)\b',
            r'\b(administration|administrative)\b',
            r'\b(service|provider)\b',
            # Generic patterns
            r'\b(the\s+\w+\s+(user|admin|manager|customer|staff))\b',
        ]
        
        for pattern in actor_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                actor = match.group(1) if match.groups() else match.group(0)
                actor = actor.strip().lower()
                # Normalize actor names
                actor_map = {
                    'administ': 'administration',
                    'administ': 'administrator',
                    'physician': 'doctor',
                    'medical staff': 'doctor',
                    'medical center': 'hospital',
                    'government of india': 'government',
                    'elderly people': 'elderly',
                    'senior citizen': 'elderly',
                    'external api': 'external api',
                    'external service': 'external api',
                    'third party': 'external api',
                }
                actor = actor_map.get(actor, actor)
                
                if actor not in actors:
                    actors.append(actor)
        
        # If no actors found, add 'System' as default
        if not actors:
            actors.append('system')
        
        return actors
    
    def _extract_modal_verbs(self, text: str) -> List[str]:
        """Extract modal verbs from requirement text."""
        modal_verbs = []
        common_modals = ['shall', 'must', 'should', 'will', 'may', 'can', 'could']
        
        for modal in common_modals:
            if re.search(r'\b' + modal + r'\b', text, re.IGNORECASE):
                modal_verbs.append(modal)
        
        return modal_verbs
    
    def _determine_category(self, text: str) -> str:
        """Determine requirement category based on keywords."""
        text_lower = text.lower()
        
        category_keywords = {
            'security': ['security', 'authenticate', 'authorize', 'encrypt', 'password', 'login'],
            'functional': ['shall', 'must', 'will', 'allow', 'enable', 'provide'],
            'non_functional': ['performance', 'response time', 'availability', 'reliability'],
            'interface': ['interface', 'api', 'endpoint', 'protocol'],
            'constraint': ['constraint', 'limit', 'maximum', 'minimum', 'shall not'],
            'data': ['data', 'store', 'save', 'retrieve', 'database']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'functional'  # Default
    
    def _generate_semantic_id(self, category: str, req_identifier: str = None) -> str:
        """Generate semantic ID for requirement."""
        prefix = 'FR' if category == 'functional' else 'NFR'
        
        if req_identifier:
            # Try to extract module from existing identifier
            parts = req_identifier.split('-')
            if len(parts) >= 2:
                return f"{prefix}-{parts[0].upper()}-{parts[1]}"
        
        # Generate default semantic ID
        module_map = {
            'functional': 'GEN',
            'security': 'SEC',
            'interface': 'INT',
            'non_functional': 'PERF',
            'constraint': 'CON',
            'data': 'DAT'
        }
        
        module_code = module_map.get(category, 'GEN')
        return f"{prefix}-{module_code}-01"
    
    def _determine_module_name(self, text: str) -> str:
        """Determine module name based on requirement content."""
        text_lower = text.lower()
        
        # More specific module keywords with priority ordering
        module_keywords = [
            ('Patient Management', ['patient', 'patients', 'patient profile', 'patient record']),
            ('Doctor Management', ['doctor', 'physician', 'medical staff', 'healthcare provider']),
            ('Hospital Administration', ['hospital', 'clinic', 'medical center', 'administration', 'administrative']),
            ('User Authentication', ['login', 'register', 'authenticate', 'password', 'credential']),
            ('Security & Compliance', ['security', 'encrypt', 'compliance', 'authorization', 'access control']),
            ('Data Management', ['data', 'store', 'save', 'retrieve', 'database', 'backup']),
            ('Payment Processing', ['payment', 'billing', 'invoice', 'transaction', 'gateway']),
            ('Document Management', ['document', 'file', 'upload', 'download', 'report']),
            ('System Configuration', ['config', 'setting', 'parameter', 'preference']),
            ('Reporting & Analytics', ['report', 'analytics', 'export', 'statistics', 'dashboard']),
            ('External Integration', ['api', 'external', 'third party', 'interface', 'integration']),
            ('Government Compliance', ['government', 'authority', 'regulation', 'compliance', 'legal']),
            ('Elderly Care', ['elderly', 'senior citizen', 'aged care', 'geriatric']),
            ('General', ['system', 'application', 'software', 'platform'])
        ]
        
        for module, keywords in module_keywords:
            if any(keyword in text_lower for keyword in keywords):
                return module
        
        return 'General'
    
    def _validate_enrichment(self, enrichment: Dict[str, Any]) -> bool:
        """Validate that enrichment data is complete and valid."""
        required_fields = ['actors_json', 'modal_verbs_json', 'category', 'semantic_id', 'module_name']
        
        for field in required_fields:
            if field not in enrichment:
                return False
            
            # Validate JSON fields can be parsed
            if field.endswith('_json'):
                try:
                    json.loads(enrichment[field])
                except json.JSONDecodeError:
                    return False
        
        return True
    
    def enrich_requirements_batch(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich multiple requirements in batch.
        
        Args:
            requirements: List of requirement dictionaries with 'text' and optional 'identifier'
            
        Returns:
            List of enriched requirement dictionaries
        """
        enriched_requirements = []
        
        for req in requirements:
            text = req.get('text') or req.get('current_text') or req.get('original_text', '')
            identifier = req.get('identifier') or req.get('req_identifier')
            
            enrichment = self.enrich_requirement(text, identifier)
            
            # Merge enrichment with original requirement
            enriched_req = {**req, **enrichment}
            enriched_requirements.append(enriched_req)
        
        logger.info(f"Enriched {len(enriched_requirements)} requirements")
        return enriched_requirements
