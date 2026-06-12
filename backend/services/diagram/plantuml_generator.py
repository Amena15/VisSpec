"""
PlantUML Syntax Generator for IEEE-Compliant Diagram Generation.

Generates IEEE-compliant PlantUML syntax for Use Case, Sequence, and Activity diagrams.
Follows UML 2.5 standards with proper notation and styling.
"""

from typing import Dict, List, Any
from backend.core.logging import get_logger

logger = get_logger(__name__)


class PlantUMLGenerator:
    """Generates PlantUML syntax for IEEE-compliant diagrams."""
    
    def generate_usecase_plantuml(self, mapping_data: Dict[str, Any]) -> str:
        """
        Generate PlantUML syntax for Use Case diagram.
        
        Args:
            mapping_data: Dictionary with actors, use cases, relationships, associations
            
        Returns:
            PlantUML syntax string
        """
        actors = mapping_data.get('actors', [])
        use_cases = mapping_data.get('use_cases', [])
        relationships = mapping_data.get('relationships', [])
        associations = mapping_data.get('associations', [])
        system_boundary = mapping_data.get('system_boundary', 'System')
        
        plantuml = []
        
        # Header with IEEE-compliant styling
        plantuml.append("@startuml")
        plantuml.append("skinparam actorStyle stickman")
        plantuml.append("skinparam packageStyle rect")
        plantuml.append("skinparam usecase {")
        plantuml.append("  BackgroundColor #FFFFFF")
        plantuml.append("  BorderColor #000000")
        plantuml.append("}")
        plantuml.append("left to right direction")
        plantuml.append("")
        
        # Define actors (from actors_json - BR-11 compliance)
        for actor in actors:
            if actor.lower() in ['system', 'database', 'external api', 'server']:
                plantuml.append(f'actor "{actor}" as {self._shorten_name(actor)} << System >>')
            else:
                plantuml.append(f'actor "{actor}" as {self._shorten_name(actor)}')
        
        plantuml.append("")
        
        # System boundary
        plantuml.append(f'rectangle "{system_boundary}" {{')
        
        # Define use cases
        for i, use_case in enumerate(use_cases):
            short_name = self._shorten_name(use_case['name'])
            plantuml.append(f'  usecase "{use_case["name"]}" as UC{i+1}')
        
        plantuml.append("")
        
        # Define relationships (include/extend)
        for rel in relationships:
            source_uc = self._find_use_case_index(rel['source'], use_cases)
            target_uc = self._find_use_case_index(rel['target'], use_cases)
            
            if source_uc and target_uc:
                if rel['type'] == 'include':
                    plantuml.append(f'  (UC{source_uc}) ..> (UC{target_uc}) : <<include>>')
                elif rel['type'] == 'extend':
                    plantuml.append(f'  (UC{source_uc}) ..> (UC{target_uc}) : <<extend>>')
        
        plantuml.append("}")
        plantuml.append("")
        
        # Define associations (actor to use case)
        for assoc in associations:
            actor_short = self._shorten_name(assoc['actor'])
            uc_index = self._find_use_case_index(assoc['use_case'], use_cases)
            
            if uc_index:
                plantuml.append(f'{actor_short} -- UC{uc_index}')
        
        plantuml.append("@enduml")
        
        return "\n".join(plantuml)
    
    def generate_sequence_plantuml(self, mapping_data: Dict[str, Any]) -> str:
        """
        Generate PlantUML syntax for Sequence diagram.
        
        Args:
            mapping_data: Dictionary with participants, messages, scenario
            
        Returns:
            PlantUML syntax string
        """
        participants = mapping_data.get('participants', [])
        messages = mapping_data.get('messages', [])
        scenario = mapping_data.get('scenario', 'Default Scenario')
        warning = mapping_data.get('warning')
        
        plantuml = []
        
        # Header with IEEE-compliant styling
        plantuml.append("@startuml")
        plantuml.append("skinparam participantPadding 20")
        plantuml.append("skinparam maxMessageSize 150")
        plantuml.append(f'title "{scenario}"')
        plantuml.append("")
        
        # Define participants
        for i, participant in enumerate(participants):
            name = participant['name']
            short_name = self._shorten_name(name)
            
            if participant['type'] == 'system':
                plantuml.append(f'participant "{name}" as {short_name}')
            else:
                plantuml.append(f'actor "{name}" as {short_name}')
        
        plantuml.append("")
        
        # Define messages with activation/deactivation
        current_active = None
        for i, msg in enumerate(messages):
            from_short = self._shorten_name(msg['from'])
            to_short = self._shorten_name(msg['to'])
            
            # Activate new participant
            if to_short != current_active:
                plantuml.append(f'activate {to_short}')
                current_active = to_short
            
            # Generate message
            if msg['type'] == 'synchronous':
                plantuml.append(f'{from_short} -> {to_short} : {msg["message"]}')
            elif msg['type'] == 'return':
                plantuml.append(f'{to_short} --> {from_short} : {msg["message"]}')
            
            # Check if this is the last message to this participant
            if i < len(messages) - 1 and messages[i + 1]['to'] != msg['to']:
                plantuml.append(f'deactivate {to_short}')
                current_active = None
        
        # Deactivate final participant
        if current_active:
            plantuml.append(f'deactivate {current_active}')
        
        # Add warning if truncated (BR-12)
        if warning:
            plantuml.append("")
            plantuml.append(f'note right')
            plantuml.append(f'  {warning}')
            plantuml.append(f'end note')
        
        plantuml.append("@enduml")
        
        return "\n".join(plantuml)
    
    def generate_activity_plantuml(self, mapping_data: Dict[str, Any]) -> str:
        """
        Generate PlantUML syntax for Activity diagram.
        
        Args:
            mapping_data: Dictionary with activities, decisions, control flow
            
        Returns:
            PlantUML syntax string
        """
        activities = mapping_data.get('activities', [])
        decisions = mapping_data.get('decisions', [])
        control_flow = mapping_data.get('control_flow', [])
        start_node = mapping_data.get('start_node', 'Start')
        end_node = mapping_data.get('end_node', 'End')
        
        plantuml = []
        
        # Header with IEEE-compliant styling
        plantuml.append("@startuml")
        plantuml.append("skinparam activity {")
        plantuml.append("  BackgroundColor #FFFFFF")
        plantuml.append("  BorderColor #000000")
        plantuml.append("}")
        plantuml.append("")
        
        # Start node
        plantuml.append(f'start')
        plantuml.append("")
        
        # Define activities
        for i, activity in enumerate(activities):
            short_name = self._shorten_name(activity['name'])
            plantuml.append(f':{activity["name"]};')
            plantuml.append(f'fork')
            plantuml.append(f'  {short_name}')
            plantuml.append(f'fork again')
        
        # Define decisions
        for decision in decisions:
            short_name = self._shorten_name(decision['name'])
            plantuml.append(f'if ({decision["name"]}) then')
            plantuml.append(f'  {short_name}')
            plantuml.append(f'endif')
        
        # Define control flow
        for flow in control_flow:
            from_short = self._shorten_name(flow['from'])
            to_short = self._shorten_name(flow['to'])
            plantuml.append(f'{from_short} --> {to_short}')
        
        # End node
        plantuml.append("")
        plantuml.append(f'end')
        
        plantuml.append("@enduml")
        
        return "\n".join(plantuml)
    
    def _shorten_name(self, name: str) -> str:
        """Generate short name for PlantUML references."""
        # Remove spaces and special characters, take first few letters
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', name)
        if len(clean_name) > 8:
            clean_name = clean_name[:8]
        return clean_name.upper() if clean_name else 'X'
    
    def _find_use_case_index(self, use_case_name: str, use_cases: List[Dict[str, Any]]) -> int:
        """Find the index of a use case by name."""
        for i, uc in enumerate(use_cases):
            if uc['name'] == use_case_name:
                return i + 1  # PlantUML uses 1-based indexing
        return None


import re  # Add import for regex operations
