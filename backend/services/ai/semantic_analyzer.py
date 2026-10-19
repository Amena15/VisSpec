import spacy
import requests
import json
from typing import Dict, List, Any
import re
from datetime import datetime

class SemanticAnalyzer:
    def __init__(self):
        """
        Initialize the semantic analyzer with spaCy model
        """
        try:
            # Load spaCy model (you may need to download it: python -m spacy download en_core_web_sm)
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Please install with: python -m spacy download en_core_web_sm")
            # Fallback to a simpler approach if model not available
            self.nlp = None

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Dual-path semantic analysis per FYP Report Section 4.8.1.
        
        Step 1: spaCy preprocessing (ALWAYS runs) - tokenization, entity extraction, modal detection
        Step 2: Path selection based on active LLM profile availability
          - Path A (Primary): configured LLM profile (Groq gpt-oss-120b default) for deep semantic understanding
          - Path B (Fallback): Rule-based heuristic when API unavailable
        Step 3: Confidence calculation with severity-weighted penalties
        Step 4: BR-10 threshold check (0.70) applied downstream
        """
        if not text.strip():
            return {
                "entities": [],
                "relations": [],
                "ambiguities": [],
                "confidence_score": 0.0,
                "method": "empty_input"
            }

        # ──────────────────────────────────────────────────────────────
        # Step 1: spaCy Preprocessing (ALWAYS runs - lightweight, fast)
        # ──────────────────────────────────────────────────────────────
        spacy_entities = self._extract_entities(text)
        spacy_ambiguities = self._identify_ambiguities(text)

        # ──────────────────────────────────────────────────────────────
        # Step 2: Path Selection (Based on active LLM profile availability)
        # ──────────────────────────────────────────────────────────────
        from core.config import settings

        if settings.llm_available:
            # ── PATH A: PRIMARY (configured LLM profile) ───────────────
            try:
                llm_analysis = self._analyze_with_llama3(text)
                
                # LLM provided results - use them directly (higher accuracy)
                if llm_analysis.get("entities") or llm_analysis.get("ambiguities"):
                    return {
                        "entities": llm_analysis.get("entities", spacy_entities),
                        "relations": llm_analysis.get("relationships", []),
                        "ambiguities": llm_analysis.get("ambiguities", []),
                        "confidence_score": self._calculate_confidence(
                            llm_analysis.get("entities", spacy_entities),
                            llm_analysis.get("ambiguities", []),
                            text
                        ),
                        "method": "llama3",
                        "explanation": "Semantic analysis using LLaMA 3 (70B) via Groq API"
                    }
            except Exception as e:
                print(f"LLaMA 3 analysis error: {e}, falling back to heuristic")
                # Fall through to Path B

        # ── PATH B: FALLBACK (Rule-based heuristic) ──────────────────
        # Used when: no API key, API call failed, or LLM returned empty results
        return self._analyze_semantic_heuristic(text, spacy_entities, spacy_ambiguities)

    def _analyze_semantic_heuristic(self, text: str, entities: List[Dict], ambiguities: List[Dict]) -> Dict[str, Any]:
        """
        FALLBACK PATH: Rule-based heuristic when LLM is unavailable.
        Lower accuracy but always functional (no internet/API key required).
        Per FYP Report Section 4.8.1 limitations paragraph.
        """
        # Extract relations using local dependency parsing
        relations = self._extract_relations_local(text, entities)
        
        # Calculate confidence with severity-weighted penalty
        confidence_score = self._calculate_confidence(entities, ambiguities, text)

        return {
            "entities": entities,
            "relations": relations,
            "ambiguities": ambiguities,
            "confidence_score": confidence_score,
            "method": "heuristic_fallback",
            "explanation": "Rule-based heuristic (LLaMA 3 unavailable or failed)"
        }

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities using spaCy with enhanced labels for requirements analysis.
        Adds custom categories: Quality Attribute, Constraint, Temporal Requirement.
        """
        if not self.nlp:
            return self._extract_entities_fallback(text)

        doc = self.nlp(text)
        entities = []

        # Standard spaCy named entities
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "description": spacy.explain(ent.label_) or "Named entity"
            })

        # Enhanced: Extract quality attributes (confidentiality, integrity, performance, etc.)
        quality_attrs = [
            "confidentiality", "integrity", "availability", "performance",
            "reliability", "usability", "maintainability", "scalability",
            "portability", "security", "privacy", "accuracy", "efficiency",
            "responsiveness", "durability", "robustness"
        ]
        for qa in quality_attrs:
            pattern = re.compile(r'\b' + re.escape(qa) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                entities.append({
                    "text": match.group(),
                    "label": "QUALITY_ATTRIBUTE",
                    "start": match.start(),
                    "end": match.end(),
                    "description": f"Quality requirement: {qa}"
                })

        # Enhanced: Extract constraints (authorization, access control, restrictions)
        constraint_patterns = [
            (r'\b(only\s+authorized\s+\w+)', "Authorization constraint"),
            (r'\b(authorized\s+\w+)', "Authorized access restriction"),
            (r'\b(access\s+(?:control|restriction|limit))', "Access control requirement"),
            (r'\b(must\s+comply\s+with)', "Compliance constraint"),
            (r'\b(cannot|shall\s+not|must\s+not)\s+\w+', "Prohibition constraint")
        ]
        for pattern, desc in constraint_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "text": match.group(),
                    "label": "CONSTRAINT",
                    "start": match.start(),
                    "end": match.end(),
                    "description": desc
                })

        # Enhanced: Extract temporal requirements (retention, duration, timing)
        temporal_patterns = [
            (r'\b(\w+\s+retention\s+period)', "Data retention requirement"),
            (r'\b(within\s+\d+\s+(hours|days|weeks|months|years))', "Time constraint"),
            (r'\b(every\s+\d+\s+(seconds?|minutes?|hours?|days?))', "Periodic requirement"),
            (r'\b(for\s+(at\s+least\s+)?\d+\s+(years?|months?|days?))', "Duration requirement"),
            (r'\b(\d+\s+years?)(?:\s+retention)?', "Retention duration")
        ]
        for pattern, desc in temporal_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "text": match.group(),
                    "label": "TEMPORAL",
                    "start": match.start(),
                    "end": match.end(),
                    "description": desc
                })

        # Enhanced: Extract actors (human roles, job titles)
        actor_keywords = [
            "user", "admin", "administrator", "manager", "operator", "staff",
            "employee", "member", "customer", "client", "patient", "doctor",
            "nurse", "teacher", "student", "supervisor", "analyst", "developer"
        ]
        seen_actor_texts = set()
        for token in doc:
            if token.pos_ == "NOUN" and token.text.lower() in actor_keywords:
                if token.text.lower() not in seen_actor_texts:
                    seen_actor_texts.add(token.text.lower())
                    entities.append({
                        "text": token.text,
                        "label": "ACTOR",
                        "start": token.idx,
                        "end": token.idx + len(token.text),
                        "description": f"Human actor/role: {token.text}"
                    })

        return entities

    def _extract_entities_fallback(self, text: str) -> List[Dict[str, Any]]:
        """
        Fallback entity extraction using regex patterns
        """
        entities = []
        
        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({
                "text": email,
                "label": "EMAIL",
                "start": text.find(email),
                "end": text.find(email) + len(email),
                "description": "Email address"
            })
        
        # Extract URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        for url in urls:
            entities.append({
                "text": url,
                "label": "URL",
                "start": text.find(url),
                "end": text.find(url) + len(url),
                "description": "Web URL"
            })
        
        # Extract phone numbers
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
        for phone in phones:
            entities.append({
                "text": phone,
                "label": "PHONE",
                "start": text.find(phone),
                "end": text.find(phone) + len(phone),
                "description": "Phone number"
            })
        
        return entities

    def _identify_ambiguities(self, text: str) -> List[Dict[str, Any]]:
        """
        Identify potential ambiguities in the text with severity levels.
        Categorizes by: HIGH (blocks implementation), MEDIUM (causes confusion), LOW (minor).
        """
        ambiguities = []
        text_lower = text.lower()

        # HIGH severity: Vague terms that block implementation
        high_severity_terms = [
            (r'\b(appropriate|appropriately)\b', "Vague term – does not specify what constitutes this requirement", "Specify exact criteria (e.g., '7 years', '24 hours', 'encrypted at rest')"),
            (r'\b(relevant\s+\w+ regulations?)\b', "Ambiguous reference – does not specify which regulations/laws", "List specific regulations (e.g., 'GDPR', 'HIPAA', 'Malaysia PDPA 2010')"),
            (r'\b(reasonable)\b', "Vague quantifier – no measurable threshold", "Define specific numeric or verifiable criteria"),
            (r'\b(timely)\b', "Vague timing – no specific deadline", "Specify exact timeframe (e.g., 'within 24 hours', 'real-time')"),
            (r'\b(adequate|adequately)\b', "Vague quality measure", "Define minimum acceptable standard or metric"),
            (r'\b(suitable)\b', "Vague suitability criteria", "Specify exact requirements for suitability"),
        ]

        # MEDIUM severity: Uncertainty indicators that cause confusion
        medium_severity_terms = [
            (r'\b(should|could|might|would|may)\b', "Weak modal verb – 'shall' or 'must' would be stronger", "Replace 'should' with 'shall' or 'must' for mandatory requirements"),
            (r'\b(authorized\s+\w+)', "Unclear authorization mechanism", "Specify how authorization is determined (e.g., 'role-based access control', 'RBAC with levels')"),
            (r'\b(as\s+needed)\b', "Unspecified trigger condition", "Define specific conditions that trigger this action"),
            (r'\b(etc\.|and\s+so\s+on|and\s+others)\b', "Incomplete specification – missing items", "List all required items explicitly"),
            (r'\b(depending\s+on|subject\s+to|if\s+applicable)\b', "Conditional uncertainty – conditions unspecified", "Define exact conditions and fallback behavior"),
            (r'\b(usually|often|typically|generally)\b', "Frequency uncertainty", "Specify exact frequency (e.g., 'daily', '99.9% of the time')"),
            (r'\b(user-friendly)\b', "Subjective quality measure", "Define measurable usability criteria (e.g., 'max 3 clicks', 'WCAG 2.1 AA compliant')"),
            (r'\b(quickly|quick)\b', "Vague timing – no specific deadline", "Specify exact timeframe (e.g., 'within 200ms', 'under 1 second')"),
            (r'\b(reliable|reliability)\b', "Vague quality measure – no specific reliability target", "Define reliability target (e.g., '99.9% uptime', 'MTBF > 1000 hours')"),
        ]

        # LOW severity: Minor vagueness
        low_severity_terms = [
            (r'\b(maybe|perhaps|possibly|sometimes|occasionally)\b', "Uncertainty indicator", "Remove or replace with definite conditions"),
            (r'\b(soon|later|eventually|when\s+possible)\b', "Vague timing", "Specify exact timing or deadline"),
            (r'\b(large|small|fast|slow|many|few|good|bad)\b', "Vague quantifier", "Replace with specific numeric values"),
            (r'\b(tbd|to\s+be\s+determined|to\s+be\s+decided)\b', "Undetermined specification", "Provide the specification before implementation"),
        ]

        # Process HIGH severity
        for pattern, description, suggestion in high_severity_terms:
            for match in re.finditer(pattern, text_lower):
                ambiguities.append({
                    "term": match.group(),
                    "position": match.start(),
                    "description": description,
                    "severity": "high",
                    "suggestion": suggestion,
                    "context": self._get_context(text, match.start(), match.end())
                })

        # Process MEDIUM severity
        for pattern, description, suggestion in medium_severity_terms:
            for match in re.finditer(pattern, text_lower):
                ambiguities.append({
                    "term": match.group(),
                    "position": match.start(),
                    "description": description,
                    "severity": "medium",
                    "suggestion": suggestion,
                    "context": self._get_context(text, match.start(), match.end())
                })

        # Process LOW severity
        for pattern, description, suggestion in low_severity_terms:
            for match in re.finditer(pattern, text_lower):
                ambiguities.append({
                    "term": match.group(),
                    "position": match.start(),
                    "description": description,
                    "severity": "low",
                    "suggestion": suggestion,
                    "context": self._get_context(text, match.start(), match.end())
                })

        return ambiguities

    def _extract_relations_local(self, text: str, entities: List[Dict]) -> List[Dict[str, Any]]:
        """
        FALLBACK PATH: Extract relations using local spaCy dependency parsing.
        Used when LLM is unavailable. Less accurate but always functional.
        
        Detects:
        - ACCESSES: actor interacts with data entity
        - COMPLIES_WITH: system must follow regulation
        - MAINTAINS: system maintains/ensures quality attribute
        """
        relations = []
        if not self.nlp or not entities:
            return relations

        doc = self.nlp(text)
        
        # Extract actors, data entities, and external systems
        actors = [e["text"].lower() for e in entities if e.get("label") in ("ACTOR", "PERSON")]
        data_entities = [e["text"].lower() for e in entities if e.get("label") in ("Data Entity", "NOUN")]
        external_systems = [e["text"].lower() for e in entities if e.get("label") == "External System"]
        quality_attrs = [e["text"].lower() for e in entities if e.get("label") == "QUALITY_ATTRIBUTE"]
        constraints = [e["text"].lower() for e in entities if e.get("label") == "CONSTRAINT"]

        # Pattern 1: Actor ACCESSES Data Entity
        # e.g., "medical staff can access patient records"
        for sent in doc.sents:
            sent_lower = sent.text.lower()
            access_verbs = ["access", "view", "read", "modify", "update", "delete", "create", "manage"]
            for verb in access_verbs:
                if verb in sent_lower:
                    for actor in actors:
                        if actor in sent_lower:
                            for entity in data_entities:
                                if entity in sent_lower and actor != entity:
                                    relations.append({
                                        "from": actor,
                                        "to": entity,
                                        "type": "ACCESSES",
                                        "description": f"{actor.title()} can {verb} {entity}"
                                    })

        # Pattern 2: System COMPLIES_WITH External System/Regulation
        # e.g., "system must comply with privacy regulations"
        comply_verbs = ["comply", "follow", "adhere", "conform", "meet"]
        for sent in doc.sents:
            sent_lower = sent.text.lower()
            for verb in comply_verbs:
                if verb in sent_lower:
                    for ext_sys in external_systems:
                        if ext_sys in sent_lower:
                            relations.append({
                                "from": "system",
                                "to": ext_sys,
                                "type": "COMPLIES_WITH",
                                "description": f"System must comply with {ext_sys}"
                            })

        # Pattern 3: System MAINTAINS Quality Attribute
        # e.g., "system shall maintain patient data confidentiality"
        maintain_verbs = ["maintain", "ensure", "preserve", "protect", "guarantee"]
        for sent in doc.sents:
            sent_lower = sent.text.lower()
            for verb in maintain_verbs:
                if verb in sent_lower:
                    for qa in quality_attrs:
                        if qa in sent_lower:
                            relations.append({
                                "from": "system",
                                "to": qa,
                                "type": "MAINTAINS",
                                "description": f"System must {verb} {qa}"
                            })

        # Pattern 4: Constraint APPLIES_TO Actor
        # e.g., "only authorized medical staff can access"
        for sent in doc.sents:
            sent_lower = sent.text.lower()
            if any(kw in sent_lower for kw in ["only", "must", "shall", "required"]):
                for constraint in constraints:
                    if constraint in sent_lower:
                        for actor in actors:
                            if actor in sent_lower:
                                relations.append({
                                    "from": constraint,
                                    "to": actor,
                                    "type": "APPLIES_TO",
                                    "description": f"Constraint applies to {actor}"
                                })

        return relations

    def _analyze_with_llama3(self, text: str) -> Dict[str, Any]:
        """
        PRIMARY PATH: Analyze text using LLaMA 3 via Groq API.
        Returns structured data: entities, ambiguities, actors, use_cases, relationships.
        Falls back to empty result if API key is not configured.
        """
        from core.config import settings

        if not settings.llm_available:
            return {"entities": [], "ambiguities": [], "actors": [], "use_cases": [], "relationships": []}

        try:
            system_prompt = (
                "You are a senior software requirements analyst. Analyze the given text and return ONLY valid JSON "
                "with these exact keys: 'entities', 'ambiguities', 'actors', 'use_cases', 'relationships'."
                "\n\nENTITIES: Extract ALL important domain entities. Use these labels:"
                "  - Actor (human users, roles like 'medical staff', 'admin')"
                "  - System Component (subsystems, modules)"
                "  - Data Entity (data objects like 'patient records', 'user profile')"
                "  - External System (regulations, third-party services, APIs)"
                "  - Quality Attribute (confidentiality, integrity, performance, availability)"
                "  - Constraint (authorization rules, access restrictions, 'only', 'must')"
                "  - Temporal Requirement (time-based rules like 'retention period', 'within 24 hours')"
                "Each entity: {text, label, start, end, description}."
                "\n\nAMBIGUITIES: Identify ALL vague, unclear, or underspecified terms. "
                "Common triggers: 'appropriate', 'relevant', 'should', 'may', 'reasonable', 'timely', 'as needed'."
                "If the text is clear, return empty array []. Do NOT include 'not found' messages."
                "Each ambiguity MUST have: {term, position, description, severity, suggestion}."
                "  - severity: 'high' (blocks implementation), 'medium' (causes confusion), 'low' (minor)"
                "  - suggestion: specific, actionable fix"
                "\n\nACTORS: Extract ONLY human users or external systems that interact with the system. "
                "Examples: Customer, Admin, Medical Staff, API, Database. "
                "Do NOT include data entities like 'Balance', 'Funds', 'Identity' as actors."
                "\n\nUSE_CASES: Extract system actions/functions as verb-noun phrases. "
                "Examples: 'Login', 'View Balance', 'Transfer Funds', 'Maintain Confidentiality'."
                "\n\nRELATIONSHIPS: Extract how entities interact. Types:"
                "  - 'association': actor performs action on entity (e.g., medical staff ACCESSES patient records)"
                "  - 'include': required sub-function (triggered by 'must', 'required', 'need to', 'shall')"
                "  - 'extend': optional/conditional function (triggered by 'may', 'optionally', 'if', 'can also')"
                "  - 'complies_with': system must follow regulation/policy"
                "Each: {from, to, type, description}."
                "\n\nReturn ONLY the JSON object, no markdown, no explanation."
            )

            user_prompt = f"Analyze: {text}"

            resp = requests.post(
                f"{settings.llm_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": settings.LLM_TEMPERATURE,
                },
                timeout=30,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

            # Extract JSON from response (strip potential markdown fences)
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            result = json.loads(content)

            # Normalize LLM entity format (LLM may use "name"/"type" instead of "text"/"label")
            for entity in result.get("entities", []):
                if "name" in entity and "text" not in entity:
                    entity["text"] = entity.pop("name")
                if "type" in entity and "label" not in entity:
                    entity["label"] = entity.pop("type")

            return {
                "entities": result.get("entities", []),
                "ambiguities": result.get("ambiguities", []),
                "actors": result.get("actors", []),
                "use_cases": result.get("use_cases", []),
                "relationships": result.get("relationships", []),
            }
        except Exception as e:
            print(f"LLaMA 3 analysis error: {e}")
            return {"entities": [], "ambiguities": [], "actors": [], "use_cases": [], "relationships": []}

    def _merge_entities(self, entities1: List[Dict], entities2: List[Dict]) -> List[Dict]:
        """
        Merge entities from different sources, removing duplicates.
        Handles inconsistent entity formats gracefully.
        """
        seen = set()
        merged = []

        for entity_list in [entities1, entities2]:
            for entity in entity_list:
                # Skip malformed entities
                if "text" not in entity:
                    continue
                key = (
                    entity["text"].lower(),
                    entity.get("start", 0),
                    entity.get("end", 0),
                )
                if key not in seen:
                    seen.add(key)
                    merged.append(entity)

        return merged

    def _calculate_confidence(self, entities: List[Dict], ambiguities: List[Dict], text: str) -> float:
        """
        Calculate confidence score based on analysis results.
        Well-written requirements with clear entities and no ambiguities score high (0.80+).
        Vague, short, or ambiguous requirements score lower.
        Penalties are weighted by severity: high=0.15, medium=0.10, low=0.05.
        """
        if not text.strip():
            return 0.0

        # Base: text length factor (longer = more analyzable, up to 0.35)
        base_score = min(len(text) / 250, 0.35)

        # Entity bonus: more entities found = better understood structure (up to 0.35)
        entity_factor = min(len(entities) * 0.07, 0.35)

        # Modality bonus: strong requirement words boost confidence
        modal_bonus = 0.1 if re.search(r'\b(shall|must|will)\b', text, re.IGNORECASE) else 0.0

        # Ambiguity penalty: weighted by severity
        severity_weights = {"high": 0.15, "medium": 0.10, "low": 0.05}
        ambiguity_penalty = sum(
            severity_weights.get(a.get("severity", "medium"), 0.10) for a in ambiguities
        )
        ambiguity_penalty = min(ambiguity_penalty, 0.50)

        confidence = base_score + entity_factor + modal_bonus - ambiguity_penalty
        return round(max(0.0, min(1.0, confidence)), 2)

    def _get_context(self, text: str, start: int, end: int, context_length: int = 50) -> str:
        """
        Get context around a position in the text
        """
        text_len = len(text)
        context_start = max(0, start - context_length)
        context_end = min(text_len, end + context_length)
        
        return text[context_start:context_end]