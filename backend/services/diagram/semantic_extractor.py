"""
Semantic Extractor for Diagram Generation.
Uses LLaMA 3 (Groq) to extract actors, use cases, and relationships.
"""
import json
import re
from typing import List, Dict, Any, Optional
from backend.core.logging import get_logger
from backend.services.ai.llm_service import GroqLLMService
from backend.services.ai.prompts import IEEE_USECASE_EXTRACTION_PROMPT

logger = get_logger(__name__)


class DiagramSemanticExtractor:
    """Extracts diagram elements using LLaMA 3 with IEEE compliance."""

    def __init__(self):
        self.llm = GroqLLMService()
        self._cache = {}

    async def extract_usecase_data(self, text: str) -> Dict[str, Any]:
        """
        Extract use case diagram data using LLaMA 3.
        Returns: actors, use_cases, includes, extends, associations
        """
        cache_key = f"usecase_{hash(text)}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        prompt = IEEE_USECASE_EXTRACTION_PROMPT.format(text=text)
        response = await self._call_llm(prompt)
        result = self._parse_json(response)

        # Validate and clean
        result = self._validate_usecase_result(result)
        self._cache[cache_key] = result
        return result

    async def extract_sequence_data(self, text: str, scenario: str = None) -> Dict[str, Any]:
        """
        Extract sequence diagram data using LLaMA 3.
        Returns: participants, messages (max 15 steps)
        """
        cache_key = f"sequence_{hash(text)}_{scenario}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        prompt = f"""
You are a requirements engineer. Extract sequence diagram data:

1. **PARTICIPANTS** – actors and system components
2. **MESSAGES** – chronological steps with "from", "to", and "message"

SCENARIO: {scenario or "General"}

TEXT:
{text}

Return ONLY this JSON:
{{
    "participants": ["Participant1", "Participant2"],
    "messages": [
        {{"from": "Actor1", "to": "System", "message": "Action"}}
    ]
}}
"""
        response = await self._call_llm(prompt)
        result = self._parse_json(response)

        # Enforce BR-12: Maximum 15 steps
        if len(result.get("messages", [])) > 15:
            logger.warning(f"Sequence diagram has {len(result['messages'])} steps, truncating to 15 (BR-12)")
            result["messages"] = result["messages"][:15]
            result["truncated"] = True

        self._cache[cache_key] = result
        return result

    async def extract_activity_data(self, text: str) -> Dict[str, Any]:
        """
        Extract activity diagram data using LLaMA 3.
        Returns: activities, decisions, flows
        """
        cache_key = f"activity_{hash(text)}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        prompt = f"""
You are a requirements engineer. Extract activity diagram data:

1. **ACTIVITIES** – steps in the process
2. **DECISIONS** – branching conditions
3. **FLOW** – order of activities

TEXT:
{text}

Return ONLY this JSON:
{{
    "activities": ["Step1", "Step2", "Step3"],
    "decisions": [{{"condition": "Condition", "yes": "StepA", "no": "StepB"}}],
    "flow": [["Step1", "Step2"], ["Step2", "Step3"]]
}}
"""
        response = await self._call_llm(prompt)
        result = self._parse_json(response)
        self._cache[cache_key] = result
        return result

    async def _call_llm(self, prompt: str) -> str:
        """Call LLaMA 3 via Groq API."""
        try:
            response = await self.llm.chat_completion(prompt, temperature=0.1)
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Fallback to rule-based extraction
            return self._fallback_extract(prompt)

    def _parse_json(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with error handling."""
        try:
            # Extract JSON block
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}")
            return {}

    def _validate_usecase_result(self, result: Dict) -> Dict:
        """Validate and clean use case extraction result."""
        # Ensure required fields exist
        result.setdefault("actors", [])
        result.setdefault("use_cases", [])
        result.setdefault("includes", [])
        result.setdefault("extends", [])
        result.setdefault("associations", [])

        # BR-11: No hallucinated actors – filter to known types
        known_actors = {"user", "customer", "admin", "administrator", "manager", 
                       "doctor", "patient", "nurse", "teller", "clerk", "system"}
        
        result["actors"] = [a for a in result["actors"] if a.lower() in known_actors or a.lower() == "system"]

        # Remove duplicate associations
        if result["associations"]:
            result["associations"] = list(set(tuple(a) for a in result["associations"]))
            result["associations"] = [list(a) for a in result["associations"]]

        return result

    def _fallback_extract(self, prompt: str) -> str:
        """Fallback rule-based extraction when LLM fails."""
        # Simple extraction from text
        text = prompt.split("TEXT:\n")[-1] if "TEXT:\n" in prompt else ""

        actors = []
        use_cases = []
        associations = []

        # Extract actors
        actor_patterns = [r'\b(User|Customer|Admin|Manager|Doctor|Patient|System)\b']
        for pattern in actor_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            actors.extend([m.capitalize() for m in matches])

        # Extract use cases (verbs + objects)
        verb_patterns = [
            (r'\b(login|logout|register|authenticate)\b', "Login/Register"),
            (r'\b(create|add|new)\s+(\w+)', "Create {}"),
            (r'\b(update|edit|modify)\s+(\w+)', "Update {}"),
            (r'\b(delete|remove)\s+(\w+)', "Delete {}"),
            (r'\b(view|list|search|browse)\s+(\w+)', "View {}"),
        ]

        for pattern, template in verb_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                if match and len(match.groups()) > 0:
                    obj = match.group(1 if len(match.groups()) == 1 else 2)
                    use_cases.append(template.format(obj.capitalize()))

        # Default fallback if nothing found
        if not actors:
            actors = ["User"]
        if not use_cases:
            use_cases = ["Login", "View Dashboard"]

        # Create associations
        for actor in actors[:2]:
            for uc in use_cases[:3]:
                associations.append([actor, uc])

        result = {
            "actors": actors[:5],
            "use_cases": use_cases[:10],
            "includes": [],
            "extends": [],
            "associations": associations[:15]
        }

        return json.dumps(result)