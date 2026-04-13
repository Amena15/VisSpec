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
        Analyze text for semantic content using spaCy and LLaMA 3
        """
        if not text.strip():
            return {
                "entities": [],
                "relations": [],
                "ambiguities": [],
                "confidence_score": 0.0
            }

        # Extract entities using spaCy if available
        entities = self._extract_entities(text)
        
        # Identify potential ambiguities
        ambiguities = self._identify_ambiguities(text)
        
        # Analyze with LLaMA 3 (using API call)
        llm_analysis = self._analyze_with_llama3(text)
        
        # Combine results
        combined_entities = self._merge_entities(entities, llm_analysis.get("entities", []))
        combined_ambiguities = ambiguities + llm_analysis.get("ambiguities", [])
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(combined_entities, combined_ambiguities, text)
        
        return {
            "entities": combined_entities,
            "relations": [],  # Relations could be extracted in a more advanced implementation
            "ambiguities": combined_ambiguities,
            "confidence_score": confidence_score
        }

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities using spaCy
        """
        if not self.nlp:
            # Fallback entity extraction using regex
            return self._extract_entities_fallback(text)
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "description": spacy.explain(ent.label_) or "Unknown entity type"
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
        Identify potential ambiguities in the text
        """
        ambiguities = []
        text_lower = text.lower()
        
        # Look for ambiguous terms
        ambiguous_terms = [
            (r'\b(maybe|perhaps|possibly|sometimes|occasionally)\b', "Uncertainty indicator"),
            (r'\b(etc\.|and so on|and others)\b', "Incomplete specification"),
            (r'\b(soon|later|eventually|when possible)\b', "Vague timing"),
            (r'\b(large|small|fast|slow|many|few)\b', "Vague quantifier"),
            (r'\b(usually|often|typically|generally)\b', "Frequency uncertainty"),
            (r'\b(should|could|might|would)\b', "Modal verb indicating uncertainty"),
            (r'\b(tbd|to be determined|to be decided)\b', "Undetermined specification"),
            (r'\b(depending on|subject to|if applicable)\b', "Conditional uncertainty")
        ]
        
        for pattern, description in ambiguous_terms:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                ambiguities.append({
                    "term": match.group(1),
                    "position": match.start(),
                    "description": description,
                    "context": self._get_context(text, match.start(), match.end())
                })
        
        return ambiguities

    def _analyze_with_llama3(self, text: str) -> Dict[str, Any]:
        """
        Analyze text using LLaMA 3 via Groq API.
        Returns structured data: entities, ambiguities, actors, use_cases, relationships.
        Falls back to empty result if API key is not configured.
        """
        from core.config import settings

        if not settings.GROQ_API_KEY:
            return {"entities": [], "ambiguities": [], "actors": [], "use_cases": [], "relationships": []}

        try:
            system_prompt = (
                "You are a senior software requirements analyst. Analyze the given text and return ONLY valid JSON "
                "with these exact keys: 'entities', 'ambiguities', 'actors', 'use_cases', 'relationships'."
                "\n\nENTITIES: Extract important domain entities with their types. "
                "Use labels like: Actor, System Component, Data Entity, External System, Process."
                "Each entity: {text, label, start, end, description}."
                "\n\nAMBIGUITIES: Only list ACTUAL ambiguities found. "
                "If the text is clear, return empty array []. "
                "Do NOT include 'not found' messages. "
                "Each: {term, position, description, context, suggestion}."
                "\n\nACTORS: Extract ONLY human users or external systems that interact with the system. "
                "Examples: Customer, Admin, Teller, User, Manager, System, API, Database. "
                "Do NOT include data entities like 'Balance', 'Funds', 'Identity' as actors."
                "\n\nUSE_CASES: Extract system actions/functions as verb-noun phrases. "
                "Examples: 'Login', 'View Balance', 'Transfer Funds', 'Approve Loan'."
                "\n\nRELATIONSHIPS: Extract three types:"
                "  - 'association': which actor performs which use case"
                "  - 'include': required sub-function (triggered by 'must', 'required', 'need to')"
                "  - 'extend': optional conditional function (triggered by 'may', 'optionally', 'can also', 'if')"
                "Each: {from, to, type}."
                "\n\nReturn ONLY the JSON object, no markdown, no explanation."
            )

            user_prompt = f"Analyze: {text}"

            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": settings.GROQ_TEMPERATURE,
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
        """
        if not text.strip():
            return 0.0

        # Base: text length factor (longer = more analyzable, up to 0.4)
        base_score = min(len(text) / 200, 0.4)

        # Entity bonus: more entities found = better understood structure (up to 0.4)
        entity_factor = min(len(entities) * 0.08, 0.4)

        # Modality bonus: strong requirement words boost confidence
        modal_bonus = 0.1 if re.search(r'\b(shall|must|will)\b', text, re.IGNORECASE) else 0.0

        # Ambiguity penalty: each real ambiguity reduces confidence
        ambiguity_penalty = min(len(ambiguities) * 0.08, 0.3)

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