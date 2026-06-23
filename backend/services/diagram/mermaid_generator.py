import json
from typing import Any, Dict, List
from backend.core.logging import get_logger

logger = get_logger(__name__)

class MermaidGenerator:
    """Generates Mermaid syntax from diagram mapping data."""
    
    def _parse_mapping(self, mapping: Any) -> dict:
        """Robustly parse mapping data to ensure it is a dictionary."""
        if isinstance(mapping, str):
            try:
                mapping = json.loads(mapping)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse mapping JSON string: {e}")
                return {}
        if not isinstance(mapping, dict):
            logger.error(f"Mapping is not a dict: {type(mapping)}")
            return {}
        # Ensure nested list fields are parsed if they arrived as strings
        for key in ['actors', 'use_cases', 'associations', 'participants', 'messages', 'activities', 'transitions']:
            if key in mapping and isinstance(mapping[key], str):
                try:
                    mapping[key] = json.loads(mapping[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return mapping

    def generate_usecase_mermaid(self, mapping: dict) -> str:
        """Generate Mermaid syntax for Use Case diagram."""
        try:
            mapping = self._parse_mapping(mapping)
            if not mapping:
                return ""
            lines = ["graph TD", ""]
            
            # Extract actors: could be list of strings or list of dicts with 'name'
            actors_raw = mapping.get('actors', [])
            actors = []
            for a in actors_raw:
                if isinstance(a, dict) and 'name' in a:
                    actors.append(a['name'])
                elif isinstance(a, str):
                    actors.append(a)
                else:
                    actors.append(str(a))
            
            actor_ids = {}
            for i, name in enumerate(actors):
                aid = f"Actor{i}"
                actor_ids[name] = aid
                lines.append(f"    {aid}[\"{name}\"]:::actor")
            
            lines.append("")
            
            # Extract use cases similarly
            use_cases_raw = mapping.get('use_cases', [])
            use_cases = []
            for u in use_cases_raw:
                if isinstance(u, dict) and 'name' in u:
                    use_cases.append(u['name'])
                elif isinstance(u, str):
                    use_cases.append(u)
                else:
                    use_cases.append(str(u))
            
            uc_ids = {}
            for i, name in enumerate(use_cases):
                uid = f"UC{i}"
                uc_ids[name] = uid
                lines.append(f"    {uid}(\"{name}\"):::usecase")
            
            lines.append("")
            
            # Associations: could be list of dicts {'actor':'X','use_case':'Y'} or list of lists/tuples
            associations = mapping.get('associations', [])
            for assoc in associations:
                if isinstance(assoc, dict):
                    actor_name = assoc.get('actor')
                    uc_name = assoc.get('use_case')
                elif isinstance(assoc, (list, tuple)) and len(assoc) >= 2:
                    actor_name = assoc[0]
                    uc_name = assoc[1]
                else:
                    continue
                if actor_name in actor_ids and uc_name in uc_ids:
                    lines.append(f"    {actor_ids[actor_name]} --- {uc_ids[uc_name]}")
            
            # Styling
            lines.append("")
            lines.append("classDef actor fill:#e1f5ff,stroke:#01579b,stroke-width:2px")
            lines.append("classDef usecase fill:#fff9c4,stroke:#f57f17,stroke-width:2px")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating Mermaid use case syntax: {e}")
            return ""
    
    # For sequence diagrams, similar fixes if needed
    def generate_sequence_mermaid(self, mapping: dict) -> str:
        """Generate Mermaid syntax for Sequence diagram."""
        try:
            mapping = self._parse_mapping(mapping)
            if not mapping:
                return ""
            lines = ["sequenceDiagram", ""]
            
            # Participants: list of strings or dicts with 'name'
            participants_raw = mapping.get('participants', [])
            participants = []
            for p in participants_raw:
                if isinstance(p, dict) and 'name' in p:
                    participants.append(p['name'])
                elif isinstance(p, str):
                    participants.append(p)
                else:
                    participants.append(str(p))
            
            p_ids = {}
            for i, name in enumerate(participants):
                pid = f"P{i}"
                p_ids[name] = pid
                lines.append(f"    participant {pid} as {name}")
            
            lines.append("")
            
            # Messages: list of dicts with 'from', 'to', 'message'
            messages = mapping.get('messages', [])
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                from_p = msg.get('from')
                to_p = msg.get('to')
                text = msg.get('message', '')[:60]
                if from_p in p_ids and to_p in p_ids:
                    arrow = "->>" if msg.get('type') == 'synchronous' else "->"
                    lines.append(f"    {p_ids[from_p]} {arrow} {p_ids[to_p]}: {text}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating Mermaid sequence syntax: {e}")
            return ""
    
    def generate_activity_mermaid(self, mapping: dict) -> str:
        """Generate Mermaid syntax for Activity diagram."""
        try:
            mapping = self._parse_mapping(mapping)
            if not mapping:
                return ""
            lines = ["graph TD", ""]
            
            activities_raw = mapping.get('activities', [])
            activities = []
            for a in activities_raw:
                if isinstance(a, dict) and 'name' in a:
                    activities.append(a['name'])
                elif isinstance(a, str):
                    activities.append(a)
                else:
                    activities.append(str(a))
            
            act_ids = {}
            for i, name in enumerate(activities):
                aid = f"A{i}"
                act_ids[name] = aid
                lines.append(f"    {aid}[\"{name}\"]:::activity")
            
            lines.append("")
            transitions = mapping.get('transitions', [])
            for t in transitions:
                if isinstance(t, dict):
                    from_act = t.get('from')
                    to_act = t.get('to')
                elif isinstance(t, (list, tuple)) and len(t) >= 2:
                    from_act = t[0]
                    to_act = t[1]
                else:
                    continue
                if from_act in act_ids and to_act in act_ids:
                    lines.append(f"    {act_ids[from_act]} --> {act_ids[to_act]}")
            
            lines.append("")
            lines.append("classDef activity fill:#fff9c4,stroke:#f57f17,stroke-width:2px")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating Mermaid activity syntax: {e}")
            return ""