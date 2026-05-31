"""
Mermaid Syntax Generator for Interactive Preview.

Generates Mermaid-compatible syntax from diagram mapping data.
This is used for live web interface rendering while PlantUML is used for official artifacts.
"""

from core.logging import get_logger

logger = get_logger(__name__)


class MermaidGenerator:
    """Generates Mermaid syntax from diagram mapping data."""
    
    def generate_usecase_mermaid(self, mapping: dict) -> str:
        """Generate Mermaid syntax for Use Case diagram."""
        try:
            lines = []
            lines.append("graph TD")
            lines.append("")  # Empty line for readability
            
            # Add actors as nodes with proper styling
            actors = mapping.get('actors', [])
            actor_ids = {}
            for i, actor in enumerate(actors):
                actor_id = f"Actor{i}"
                actor_ids[actor['name']] = actor_id
                # Use different styling for actors vs use cases
                lines.append(f"    {actor_id}[\"{actor['name']}\"]:::actor")
            
            lines.append("")
            
            # Add use cases
            use_cases = mapping.get('use_cases', [])
            use_case_ids = {}
            for i, uc in enumerate(use_cases):
                uc_id = f"UC{i}"
                use_case_ids[uc['name']] = uc_id
                lines.append(f"    {uc_id}(\"{uc['name']}\"):::usecase")
            
            lines.append("")
            
            # Add associations
            associations = mapping.get('associations', [])
            for assoc in associations:
                actor_name = assoc['actor']
                uc_name = assoc['use_case']
                if actor_name in actor_ids and uc_name in use_case_ids:
                    lines.append(f"    {actor_ids[actor_name]} --> {use_case_ids[uc_name]}")
            
            lines.append("")
            
            # Add include/extend relationships
            for uc in use_cases:
                uc_name = uc['name']
                if uc_name in use_case_ids:
                    if uc.get('included_by'):
                        for included in uc['included_by']:
                            if included in use_case_ids:
                                lines.append(f"    {use_case_ids[included]} -.-> {use_case_ids[uc_name]} : <<include>>")
                    if uc.get('extended_by'):
                        for extended in uc['extended_by']:
                            if extended in use_case_ids:
                                lines.append(f"    {use_case_ids[extended]} -.-> {use_case_ids[uc_name]} : <<extend>>")
            
            # Add styling
            lines.append("")
            lines.append("classDef actor fill:#e1f5ff,stroke:#01579b,stroke-width:2px")
            lines.append("classDef usecase fill:#fff9c4,stroke:#f57f17,stroke-width:2px")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating Mermaid use case syntax: {e}")
            return ""
    
    def generate_sequence_mermaid(self, mapping: dict) -> str:
        """Generate Mermaid syntax for Sequence diagram."""
        try:
            lines = []
            lines.append("sequenceDiagram")
            lines.append("")
            
            # Add participants with proper ordering
            participants = mapping.get('participants', [])
            participant_ids = {}
            for i, participant in enumerate(participants):
                participant_id = f"P{i}"
                participant_ids[participant['name']] = participant_id
                # Use as for clear naming
                lines.append(f"    participant {participant_id} as {participant['name']}")
            
            lines.append("")
            
            # Add messages with proper direction and content
            messages = mapping.get('messages', [])
            for msg in messages:
                from_participant = msg['from']
                to_participant = msg['to']
                message_text = msg['message'][:60]  # Limit message length for readability
                
                if from_participant in participant_ids and to_participant in participant_ids:
                    # Use different arrow styles based on message type
                    arrow_style = "->>" if msg.get('type') == 'synchronous' else "->"
                    lines.append(f"    {participant_ids[from_participant]} {arrow_style} {participant_ids[to_participant]}: {message_text}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating Mermaid sequence syntax: {e}")
            return ""
    
    def generate_activity_mermaid(self, mapping: dict) -> str:
        """Generate Mermaid syntax for Activity diagram."""
        try:
            lines = []
            lines.append("graph TD")
            lines.append("")  # Empty line for readability
            
            # Add activities with proper styling
            activities = mapping.get('activities', [])
            activity_ids = {}
            for i, activity in enumerate(activities):
                activity_id = f"A{i}"
                activity_ids[activity['name']] = activity_id
                # Use different shapes based on activity type
                if activity.get('type') == 'start':
                    lines.append(f"    {activity_id}(\"{activity['name']}\"):::start")
                elif activity.get('type') == 'end':
                    lines.append(f"    {activity_id}(\"{activity['name']}\"):::end")
                else:
                    lines.append(f"    {activity_id}[\"{activity['name']}\"]:::activity")
            
            lines.append("")
            
            # Add transitions with proper labels
            transitions = mapping.get('transitions', [])
            for transition in transitions:
                from_activity = transition['from']
                to_activity = transition['to']
                label = transition.get('label', '')
                
                if from_activity in activity_ids and to_activity in activity_ids:
                    if label:
                        lines.append(f"    {activity_ids[from_activity]} -->|{label}| {activity_ids[to_activity]}")
                    else:
                        lines.append(f"    {activity_ids[from_activity]} --> {activity_ids[to_activity]}")
            
            # Add styling
            lines.append("")
            lines.append("classDef start fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px")
            lines.append("classDef end fill:#ffcdd2,stroke:#c62828,stroke-width:2px")
            lines.append("classDef activity fill:#fff9c4,stroke:#f57f17,stroke-width:2px")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating Mermaid activity syntax: {e}")
            return ""
