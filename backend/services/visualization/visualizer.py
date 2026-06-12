"""
Visualization service for generating Mermaid and PlantUML diagrams from requirements text.
Uses LLaMA 3 (via Groq API) semantic analysis for intelligent extraction,
with spaCy + rule-based fallback when LLM is unavailable.
"""
import re
from typing import Dict, List, Any, Set
from datetime import datetime

import spacy
from backend.services.ai.semantic_analyzer import SemanticAnalyzer


def _normalize_actor(name: str) -> str:
    """Normalize actor name to singular, title-case form."""
    singular_map = {
        "users": "user",
        "customers": "customer",
        "admins": "admin",
        "administrators": "administrator",
        "systems": "system",
        "clients": "client",
        "guests": "guest",
        "managers": "manager",
        "operators": "operator",
        "tellers": "teller",
        "clerks": "clerk",
    }
    lower = name.lower()
    if lower in singular_map:
        name = singular_map[lower]
    return name.strip().title()


def _safe_id(text: str) -> str:
    """Convert text to a safe Mermaid identifier."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', text)


class Visualizer:
    """Generates Mermaid and PlantUML diagrams using LLM semantic analysis."""

    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Please install with: python -m spacy download en_core_web_sm")
            self.nlp = None

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def generate_visualization(self, text: str, diagram_type: str, options: Dict = None) -> Dict[str, Any]:
        """Dispatch to the correct diagram generator.

        Always uses the LLM semantic analyzer for intelligent extraction.
        Falls back to rule-based when Groq API key is not set.
        Returns both Mermaid and PlantUML formats.
        """
        generators = {
            "usecase": self.generate_usecase_diagram,
            "sequence": self.generate_sequence_diagram,
            "activity": self.generate_activity_diagram,
        }
        gen = generators.get(diagram_type)
        if not gen:
            raise ValueError(f"Unsupported diagram type: {diagram_type}")

        result = gen(text)
        result["plantuml_syntax"] = self._to_plantuml(diagram_type, result)
        return result

    def generate_usecase_diagram(self, text: str) -> Dict[str, Any]:
        """Generate UML Use Case diagram using LLM semantic analysis."""
        # Step 1: Semantic analysis (LLaMA 3 or fallback)
        semantic = self.semantic_analyzer.analyze_text(text)

        # Step 2: Extract structured data from LLM output
        actors = semantic.get("actors", [])
        use_cases = semantic.get("use_cases", [])
        relationships = semantic.get("relationships", [])

        # If LLM didn't return actors/use_cases, fall back to rule-based
        if not actors:
            actors = self._extract_actors_fallback(text)
        if not use_cases:
            use_cases = self._extract_use_cases_fallback(text)
        if not relationships:
            relationships = self._extract_relationships_fallback(text, actors, use_cases)

        # Normalize actors
        actors = [_normalize_actor(a) if isinstance(a, str) else _normalize_actor(a.get("name", a.get("text", ""))) for a in actors]
        actors = sorted(set(actors))

        # Normalize use cases
        use_cases = [uc if isinstance(uc, str) else uc.get("name", uc.get("text", "")) for uc in use_cases]
        use_cases = sorted(set(uc for uc in use_cases if len(uc) > 2))[:15]

        # Normalize relationships
        normalized_rels = []
        for rel in relationships:
            rel_type = rel.get("type", "association")
            if rel_type in ("uses", "association"):
                rel_type = "association"
            normalized_rels.append({
                "from": _normalize_actor(rel.get("from", "")),
                "to": rel.get("to", rel.get("use_case", "")),
                "type": rel_type,
            })

        # Post-process: detect include/extend from text patterns
        normalized_rels = self._enrich_relationships(text, use_cases, normalized_rels)

        # Extract system title
        title = self._extract_title(text)

        # Step 3: Generate diagrams
        mermaid = self._generate_usecase_mermaid(actors, use_cases, normalized_rels, title)

        return {
            "mermaid_syntax": mermaid,
            "text": text,
            "actors": actors,
            "use_cases": use_cases,
            "relationships": normalized_rels,
            "title": title,
            "description": f"Generated from text with {len(actors)} actors and {len(use_cases)} use cases",
        }

    def generate_sequence_diagram(self, text: str) -> Dict[str, Any]:
        """Generate UML Sequence diagram using LLM semantic analysis."""
        semantic = self.semantic_analyzer.analyze_text(text)

        participants = semantic.get("actors", [])
        if not participants:
            participants = self._extract_actors_fallback(text)

        participants = [_normalize_actor(p) if isinstance(p, str) else _normalize_actor(p.get("name", "")) for p in participants]
        participants = sorted(set(participants))
        participants.append("System")  # always include system

        # Extract messages from LLM relationships or fallback
        messages = []
        for rel in semantic.get("relationships", []):
            if rel.get("type") == "association":
                messages.append({
                    "sender": _normalize_actor(rel.get("from", "")),
                    "message": rel.get("to", ""),
                    "receiver": "System",
                })

        if not messages:
            # Fallback: create simple sequential messages from use cases
            use_cases = semantic.get("use_cases", [])
            for i, uc in enumerate(use_cases[:8]):
                sender = participants[0] if participants else "User"
                messages.append({
                    "sender": sender,
                    "message": uc,
                    "receiver": "System",
                })

        mermaid = self._generate_sequence_mermaid(participants, messages)

        return {
            "mermaid_syntax": mermaid,
            "text": text,
            "participants": participants,
            "messages": messages,
            "title": "Sequence Diagram",
            "description": f"Generated from text with {len(participants)} participants and {len(messages)} messages",
        }

    def generate_activity_diagram(self, text: str) -> Dict[str, Any]:
        """Generate Activity diagram using LLM semantic analysis."""
        semantic = self.semantic_analyzer.analyze_text(text)

        activities = semantic.get("use_cases", [])
        if not activities:
            activities = self._extract_use_cases_fallback(text)

        activities = [a if isinstance(a, str) else a.get("name", a.get("text", "")) for a in activities]
        activities = [a for a in activities if len(a) > 2][:12]

        mermaid = self._generate_activity_mermaid(activities)

        return {
            "mermaid_syntax": mermaid,
            "text": text,
            "activities": activities,
            "title": "Activity Diagram",
            "description": f"Generated from text with {len(activities)} activities",
        }

    # ------------------------------------------------------------------ #
    #  PlantUML Generation
    # ------------------------------------------------------------------ #

    def _to_plantuml(self, diagram_type: str, result: Dict[str, Any]) -> str:
        """Convert extracted diagram data to PlantUML syntax."""
        if diagram_type == "usecase":
            return self._plantuml_usecase(result)
        elif diagram_type == "sequence":
            return self._plantuml_sequence(result)
        elif diagram_type == "activity":
            return self._plantuml_activity(result)
        return ""

    def _plantuml_usecase(self, result: Dict[str, Any]) -> str:
        """Generate PlantUML use case diagram syntax following IEEE/UML standards."""
        lines = ["@startuml", ""]
        
        # IEEE/UML standard styling
        lines.append("skinparam actorStyle stickman")
        lines.append("skinparam packageStyle rect")
        lines.append("skinparam rectangleStyle rounded")
        lines.append("skinparam usecaseStyle ellipse")
        lines.append("left to right direction")
        lines.append("")

        actors = result.get("actors", [])
        use_cases = result.get("use_cases", [])
        relationships = result.get("relationships", [])

        title = result.get("title", "System")
        
        # Define actors with IEEE stickman notation
        for actor in actors:
            # Mark external systems as machines
            if actor.lower() in ["database", "system", "api", "server"]:
                lines.append(f'actor "{actor}" as {_safe_id(actor)} << Machine >>')
            else:
                lines.append(f'actor "{actor}" as {_safe_id(actor)}')
        
        lines.append("")

        # System boundary with proper IEEE notation
        lines.append(f'rectangle "{title}" {{')
        lines.append("")

        # Define use cases within system boundary
        for uc in use_cases:
            safe = _safe_id(uc)
            lines.append(f'    usecase "{uc}" as {safe}')

        lines.append("")
        lines.append("}")
        lines.append("")

        # Process relationships with IEEE standard notation
        for rel in relationships:
            rel_type = rel.get("type", "association")
            from_name = rel.get("from", "")
            to_name = rel.get("to", "")
            from_safe = _safe_id(from_name)
            to_safe = _safe_id(to_name)

            if rel_type == "include":
                # IEEE Standard: Dashed lines for include
                lines.append(f'    ({to_safe}) ..> ({from_safe}) : <<include>>')
            elif rel_type == "extend":
                # IEEE Standard: Dashed lines for extend
                lines.append(f'    ({to_safe}) ..> ({from_safe}) : <<extend>>')
            else:
                # IEEE Standard: Solid lines for associations
                lines.append(f'    {from_safe} -- {to_safe}')

        lines.append("")
        lines.append("@enduml")
        return "\n".join(lines)

    def _plantuml_sequence(self, result: Dict[str, Any]) -> str:
        """Generate PlantUML sequence diagram syntax following IEEE/UML standards."""
        lines = ["@startuml", "sequence", ""]
        
        # IEEE/UML standard styling for sequence diagrams
        lines.append("skinparam participantPadding 20")
        lines.append("skinparam boxPadding 20")
        lines.append("skinparam rectangleStyle rounded")
        lines.append("skinparam sequenceMessageAlign center")
        lines.append("skinparam sequenceLifeLineBorder #333333")
        lines.append("skinparam sequenceArrowColor #333333")
        lines.append("")

        participants = result.get("participants", [])
        messages = result.get("messages", [])

        # Define participants with IEEE standard notation
        for p in participants:
            safe = p.replace(" ", "_")
            # Mark external systems/machines
            if p.lower() in ["database", "system", "api", "server"]:
                lines.append(f'participant "{p}" as {safe} << Machine >>')
            else:
                lines.append(f'participant "{p}" as {safe}')

        lines.append("")

        # Process messages with IEEE standard notation
        if messages:
            for i, msg in enumerate(messages):
                sender = msg["sender"].replace(" ", "_")
                receiver = msg["receiver"].replace(" ", "_")
                message_text = msg["message"]
                
                # Truncate long messages for readability
                if len(message_text) > 50:
                    message_text = message_text[:47] + "..."
                
                # IEEE Standard: Solid lines for synchronous calls
                lines.append(f'    {sender} -> {receiver} : {message_text}')
                
                # Add activation/deactivation for better visualization
                if i == 0:
                    lines.append(f'    activate {receiver}')
                elif i < len(messages) - 1:
                    next_receiver = messages[i + 1]["receiver"].replace(" ", "_")
                    if receiver != next_receiver:
                        lines.append(f'    deactivate {receiver}')
                        lines.append(f'    activate {next_receiver}')
        else:
            # Default interaction if no messages
            if len(participants) >= 2:
                first = participants[0].replace(" ", "_")
                second = participants[1].replace(" ", "_")
                lines.append(f'    {first} -> {second} : Initialize Process')
                lines.append(f'    activate {second}')
                lines.append(f'    {second} --> {first} : Response')
                lines.append(f'    deactivate {second}')

        lines.append("")
        lines.append("@enduml")
        return "\n".join(lines)

    def _plantuml_activity(self, result: Dict[str, Any]) -> str:
        """Generate PlantUML activity diagram syntax."""
        lines = ["@startuml", "skinparam backgroundColor white", ""]

        activities = result.get("activities", [])

        lines.append("    start")
        for activity in activities:
            lines.append(f'    :{activity};')
        lines.append("    stop")
        lines.append("@enduml")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Mermaid Generation
    # ------------------------------------------------------------------ #

    def _generate_usecase_mermaid(self, actors: List[str], use_cases: List[str],
                                   relationships: List[Dict[str, str]],
                                   title: str) -> str:
        """Generate Mermaid syntax following IEEE/UML standards with stickman actors."""
        lines = ["graph TD"]

        # System title
        safe_title = title.replace('"', '#quot;')
        lines.append(f'    Title["{safe_title}"]')
        lines.append('    classDef titleStyle fill:none,stroke:none,font-size:18px,text-align:center,font-weight:bold')
        lines.append('    class Title titleStyle')
        lines.append("")

        # Actors with stickman representation (IEEE standard)
        for i, actor in enumerate(actors):
            safe = f"Actor{i}"
            safe_label = actor.replace('"', '#quot;')
            # Use Unicode stickman symbol for IEEE standard representation
            lines.append(f'    {safe}["<div style=\'font-size:24px;text-align:center\'>&#128100;<br/><small>{safe_label}</small></div>"]')

        lines.append("")

        # System boundary with proper IEEE styling
        lines.append('    subgraph System["System Boundary"]')
        lines.append('        direction TB')
        lines.append('        classDef systemStyle fill:#F8F9FA,stroke:#333333,stroke-width:2px,font-weight:bold')
        lines.append('        class System systemStyle')
        lines.append("")

        # Use cases with oval shape (UML standard)
        for i, uc in enumerate(use_cases):
            safe = f"UC{i}"
            safe_label = uc.replace('"', '#quot;')
            # Truncate long use case names for better readability
            display_label = safe_label[:30] + "..." if len(safe_label) > 30 else safe_label
            lines.append(f'        {safe}["{display_label}"]')

        lines.append("    end")
        lines.append("")

        # Relationships with proper IEEE notation
        assoc_rels = [r for r in relationships if r["type"] == "association"]
        include_extends = [r for r in relationships if r["type"] in ("include", "extend")]

        # Actor -> Use Case associations (solid lines)
        for rel in assoc_rels:
            actor_idx = next((i for i, a in enumerate(actors) if a == rel["from"]), None)
            uc_idx = next((i for i, uc in enumerate(use_cases) if uc == rel["to"]), None)

            if actor_idx is not None and uc_idx is not None:
                lines.append(f"    Actor{actor_idx} --> UC{uc_idx}")

        # Include/Extend relationships (dashed lines with proper notation)
        for rel in include_extends:
            from_idx = next((i for i, uc in enumerate(use_cases) if uc == rel["from"]), None)
            to_idx = next((i for i, uc in enumerate(use_cases) if uc == rel["to"]), None)

            if from_idx is not None and to_idx is not None:
                if rel["type"] == "include":
                    lines.append(f"    UC{from_idx} -.-> UC{to_idx}")
                    lines.append(f"    UC{from_idx}:::includeEdge -.-> UC{to_idx}:::includeEdge")
                else:  # extend
                    lines.append(f"    UC{from_idx} ..> UC{to_idx}")
                    lines.append(f"    UC{from_idx}:::extendEdge ..> UC{to_idx}:::extendEdge")

        # IEEE standard styling
        lines.append("")
        lines.append("    %% IEEE/UML Standard Styling")
        lines.append('    classDef actorStyle fill:#E3F2FD,stroke:#1976D2,stroke-width:2px,color:#0D47A1,font-size:12px')
        lines.append('    classDef usecaseStyle fill:#FFFFFF,stroke:#424242,stroke-width:2px,color:#212121,font-size:11px,shape:ellipse')
        lines.append('    classDef includeEdge stroke:#FF9800,stroke-width:2px,stroke-dasharray: 5 5')
        lines.append('    classDef extendEdge stroke:#4CAF50,stroke-width:2px,stroke-dasharray: 3 3')

        # Apply styles
        if actors:
            actor_ids = ",".join(f"Actor{i}" for i in range(len(actors)))
            lines.append(f'    class {actor_ids} actorStyle')

        if use_cases:
            uc_ids = ",".join(f"UC{i}" for i in range(len(use_cases)))
            lines.append(f'    class {uc_ids} usecaseStyle')

        # Add legend for IEEE notation
        lines.append("")
        lines.append("    %% Legend")
        lines.append('    subgraph Legend["IEEE/UML Notation"]')
        lines.append('        direction LR')
        lines.append('        L1["Actor (Stickman)"]')
        lines.append('        L2["Use Case (Oval)"]')
        lines.append('        L3["Include (Dashed)"]')
        lines.append('        L4["Extend (Dotted)"]')
        lines.append('        classDef legendStyle fill:#F5F5F5,stroke:#999999,stroke-width:1px')
        lines.append('        class Legend legendStyle')
        lines.append('        class L1 actorStyle')
        lines.append('        class L2 usecaseStyle')
        lines.append('        class L3 includeEdge')
        lines.append('        class L4 extendEdge')
        lines.append('    end')

        return "\n".join(lines)

    def _generate_sequence_mermaid(self, participants: List[str], messages: List[Dict[str, str]]) -> str:
        """Generate Mermaid sequence diagram syntax following IEEE/UML standards."""
        lines = ["sequenceDiagram"]

        # Add title
        lines.append('    title Sequence Diagram - IEEE/UML Standard')
        lines.append("")

        # Define participants with proper IEEE styling
        for i, p in enumerate(participants):
            safe = p.replace(" ", "_")
            # Use different styling for actors vs system components
            # Note: Mermaid doesn't support HTML formatting in participant names
            lines.append(f'    participant "{p}" as {safe}')

        lines.append("")

        # Process messages with proper IEEE notation
        if messages:
            for i, msg in enumerate(messages):
                sender = msg["sender"].replace(" ", "_")
                receiver = msg["receiver"].replace(" ", "_")
                message_text = msg["message"]
                
                # Truncate very long messages for better readability
                if len(message_text) > 50:
                    message_text = message_text[:47] + "..."
                
                # Use solid lines for synchronous communication (IEEE standard)
                lines.append(f'    {sender}->>{receiver}: {message_text}')
                
                # Add activation boxes for better visualization
                if i == 0:
                    lines.append(f'    activate {receiver}')
                elif i < len(messages) - 1:
                    next_receiver = messages[i + 1]["receiver"].replace(" ", "_")
                    if receiver != next_receiver:
                        lines.append(f'    deactivate {receiver}')
                        lines.append(f'    activate {next_receiver}')
        else:
            # Default interaction if no messages
            if len(participants) >= 2:
                first = participants[0].replace(" ", "_")
                second = participants[1].replace(" ", "_")
                lines.append(f'    {first}->>{second}: Initialize Process')
                lines.append(f'    activate {second}')
                lines.append(f'    {second}-->>{first}: Response')
                lines.append(f'    deactivate {second}')

        # Add IEEE/UML notation legend
        lines.append("")
        lines.append("    %% IEEE/UML Notation Legend")
        lines.append("    Note over Participant: ->> Synchronous Call")
        lines.append("    Note over Participant: -->> Return Message")
        lines.append("    Note over Participant: activate/deactivate Lifeline")

        return "\n".join(lines)

    def _generate_activity_mermaid(self, activities: List[str]) -> str:
        """Generate Mermaid activity diagram syntax."""
        lines = ["graph TD", '    Start([Start])']

        for i, act in enumerate(activities):
            safe = f"A{i}"
            lines.append(f'    {safe}["{act}"]')

        if activities:
            lines.append("    Start --> A0")
            for i in range(len(activities) - 1):
                lines.append(f"    A{i} --> A{i + 1}")
            lines.append(f"    A{len(activities) - 1} --> End")

        lines.append('    End([End])')
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Fallback Rule-Based Extraction (when LLM is unavailable)
    # ------------------------------------------------------------------ #

    def _extract_actors_fallback(self, text: str) -> List[str]:
        """Fallback actor extraction using strict whitelist."""
        actors: Set[str] = set()
        known_actors = {
            "user", "customer", "admin", "administrator", "manager", "operator",
            "guest", "client", "vendor", "staff", "employee", "member",
            "student", "teacher", "instructor", "supervisor", "director",
            "agent", "representative", "analyst", "developer", "tester",
            "patient", "doctor", "nurse", "teller", "clerk",
            "system", "server", "database", "api", "service", "application",
        }

        if self.nlp:
            doc = self.nlp(text)
            for token in doc:
                if token.pos_ not in ("PROPN", "NOUN"):
                    continue
                normalized = _normalize_actor(token.text)
                if normalized.lower() in known_actors:
                    sent = token.sent.text.lower()
                    if any(kw in sent for kw in ["can", "shall", "must", "should", "will", "may"]):
                        actors.add(normalized)

        for pattern in [
            r'\b([A-Z][a-z]+)s? can\b', r'\b([A-Z][a-z]+)s? shall\b',
            r'\b([A-Z][a-z]+)s? must\b', r'allows?\s+([A-Z][a-z]+)s?\s+to\b',
        ]:
            for match in re.finditer(pattern, text):
                candidate = _normalize_actor(match.group(1))
                if candidate.lower() in known_actors:
                    actors.add(candidate)

        if len(actors) > 2:
            actors.discard("System")
            actors.discard("User")

        return sorted(actors)[:8]

    def _extract_use_cases_fallback(self, text: str) -> List[str]:
        """Fallback use case extraction."""
        use_cases: Set[str] = set()
        skip_verbs = {"have", "be", "do", "make", "get", "take", "know", "see", "come", "go", "say"}

        if self.nlp:
            doc = self.nlp(text)
            for sent in doc.sents:
                for token in sent:
                    if token.pos_ == "VERB" and token.lemma_.lower() not in skip_verbs:
                        for child in token.children:
                            if child.dep_ in ("dobj", "attr"):
                                uc = f"{token.lemma_.title()} {child.text.title()}"
                                if len(uc) > 4:
                                    use_cases.add(uc)

        for pattern in [
            r'(?:can|could)\s+(.+?)(?:\.|,|and\b|or\b|$)',
            r'(?:shall|must|should|will)\s+(?:be\s+)?(?:able\s+to\s+)?(.+?)(?:\.|,|$)',
        ]:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                phrase = match.group(1).strip()
                if 4 < len(phrase) < 80:
                    cleaned = phrase.rstrip(".,;!?").title()
                    if not re.match(r'^(Has|Have|Is|Are|Was|Were)\b', cleaned):
                        use_cases.add(cleaned)

        return sorted(use_cases)[:12]

    def _extract_relationships_fallback(self, text: str, actors: List[str], use_cases: List[str]) -> List[Dict[str, str]]:
        """Fallback relationship extraction using sentence proximity."""
        relationships = []
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

        for sentence in sentences:
            sent_lower = sentence.lower()
            sentence_actors = [a for a in actors if a.lower() in sent_lower]
            if not sentence_actors:
                continue

            sentence_ucs = []
            for uc in use_cases:
                uc_words = uc.lower().split()
                matches = sum(1 for w in uc_words if w in sent_lower)
                if matches >= min(2, len(uc_words)):
                    sentence_ucs.append(uc)

            for actor in sentence_actors:
                for uc in sentence_ucs:
                    if not any(r["from"] == actor and r["to"] == uc for r in relationships):
                        relationships.append({"from": actor, "to": uc, "type": "association"})

        if not relationships and actors and use_cases:
            for actor in actors:
                for uc in use_cases:
                    relationships.append({"from": actor, "to": uc, "type": "association"})

        return relationships

    def _extract_title(self, text: str) -> str:
        """Extract a short system title from the text."""
        match = re.search(r'(?:the|an|a)\s+(\w+\s+(?:\w+\s+)?system)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()

        match = re.search(r'(\w+\s+system)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip().title()

        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if sentences:
            first = sentences[0]
            if len(first) > 40:
                return first[:37].rstrip() + "..."
            return first

        return "System"

    def _enrich_relationships(self, text: str, use_cases: List[str], relationships: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Detect include/extend relationships from text keyword patterns."""
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

        for sentence in sentences:
            sent_lower = sentence.lower()

            # Include: mandatory sub-steps (must, required, need to, then)
            for marker in ["must", "required", "need to", "needs to", "then"]:
                if marker in sent_lower:
                    source_uc = self._match_uc(sent_lower, use_cases)
                    after = sent_lower.split(marker, 1)[-1]
                    target_uc = self._match_uc(after, use_cases)
                    if source_uc and target_uc and source_uc != target_uc:
                        if not any(r["from"] == source_uc and r["to"] == target_uc for r in relationships):
                            relationships.append({"from": source_uc, "to": target_uc, "type": "include"})

            # Extend: optional/conditional (if, may, optionally, can also, in case)
            for marker in ["if", "may", "optionally", "can also", "in case", "otherwise"]:
                if marker in sent_lower:
                    source_uc = self._match_uc(sent_lower, use_cases)
                    after = sent_lower.split(marker, 1)[-1]
                    target_uc = self._match_uc(after, use_cases)
                    if source_uc and target_uc and source_uc != target_uc:
                        if not any(r["from"] == source_uc and r["to"] == target_uc for r in relationships):
                            relationships.append({"from": source_uc, "to": target_uc, "type": "extend"})

        return relationships

    def _match_uc(self, text: str, use_cases: List[str]) -> str:
        """Find which use case best matches a piece of text."""
        best_match = None
        best_score = 0
        for uc in use_cases:
            uc_lower = uc.lower()
            uc_words = set(uc_lower.split())
            matches = sum(1 for w in uc_words if w in text)
            if uc_lower in text:
                matches = len(uc_words) + 2
            if matches > best_score:
                best_score = matches
                best_match = uc
        return best_match if best_score >= 1 else None
