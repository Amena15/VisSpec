"""
Sequence Diagram Mapping Service for IEEE-Compliant Diagram Generation.

Maps enriched requirements to Sequence diagram elements following IEEE UML standards.
Enforces BR-12: Maximum 15 steps per sequence diagram.
"""

import json
import re
from typing import Dict, List, Any, Set
from collections import defaultdict

from backend.core.logging import get_logger

logger = get_logger(__name__)


class SequenceMapper:
    """Maps requirements to Sequence diagram elements."""
    
    MAX_STEPS = 15  # BR-12 compliance
    
    def __init__(self):
        self.sequential_keywords = ['first', 'then', 'next', 'after', 'before', 'finally', 'subsequently']
        self.system_participants = ['System', 'Database', 'External API', 'Server', 'Service']
    
    def map_requirements_to_sequence(self, requirements: List[Dict[str, Any]], 
                                     scenario: str = None) -> Dict[str, Any]:
        """
        Map enriched requirements to Sequence diagram elements.
        
        Args:
            requirements: List of enriched requirement dictionaries
            scenario: Optional scenario name to filter requirements
            
        Returns:
            Dictionary with participants, messages, and warnings
        """
        # Extract participants from actors_json and system components
        participants = self._extract_participants(requirements)
        
        # Extract messages from functional requirements
        messages = self._extract_messages(requirements, scenario)
        
        # Enforce BR-12: Maximum 15 steps
        if len(messages) > self.MAX_STEPS:
            logger.warning(f"Sequence diagram has {len(messages)} steps, truncating to {self.MAX_STEPS} (BR-12)")
            messages = messages[:self.MAX_STEPS]
        
        return {
            'participants': participants,
            'messages': messages,
            'scenario': scenario or 'Default Scenario',
            'step_count': len(messages),
            'truncated': len(messages) == self.MAX_STEPS,
            'warning': f"Sequence diagram truncated to {self.MAX_STEPS} steps (BR-12)" if len(messages) == self.MAX_STEPS else None
        }
    
    def _extract_participants(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract participants from requirements.
        Participants include actors from actors_json and system components.
        """
        participants_set = set()
        
        # Add actors from requirements (BR-11 compliance - no hallucinated actors)
        for req in requirements:
            actors_json = req.get('actors_json')
            if actors_json:
                try:
                    actors = json.loads(actors_json)
                    for actor in actors:
                        normalized_actor = self._normalize_participant_name(actor)
                        if normalized_actor:
                            participants_set.add(normalized_actor)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid actors_json in requirement")
        
        # Add system participants
        for sys_participant in self.system_participants:
            participants_set.add(sys_participant)
        
        # Convert to participant objects with types
        participants = []
        for participant in sorted(participants_set):
            participant_type = self._determine_participant_type(participant)
            participants.append({
                'name': participant,
                'type': participant_type
            })
        
        return participants
    
    def _normalize_participant_name(self, name: str) -> str:
        """Normalize participant name to consistent format."""
        name = name.strip()
        return ' '.join(word.capitalize() for word in name.split())
    
    def _determine_participant_type(self, name: str) -> str:
        """Determine participant type (actor or system)."""
        if name in self.system_participants:
            return 'system'
        return 'actor'
    
    def _extract_messages(self, requirements: List[Dict[str, Any]], 
                         scenario: str = None) -> List[Dict[str, Any]]:
        """
        Extract messages from requirements based on sequential keywords.
        Messages represent step-by-step interactions between participants.
        """
        messages = []
        
        # Filter requirements by scenario if provided
        if scenario:
            requirements = [req for req in requirements 
                          if self._matches_scenario(req, scenario)]
        
        # Sort requirements by sequence_order if available
        requirements = sorted(requirements, 
                           key=lambda x: x.get('sequence_order', 0))
        
        for req in requirements:
            text = req.get('current_text') or req.get('original_text', '')
            req_id = req.get('req_id')
            actors_json = req.get('actors_json')
            
            # Extract participants from this requirement
            req_participants = []
            if actors_json:
                try:
                    actors = json.loads(actors_json)
                    req_participants = [self._normalize_participant_name(a) for a in actors]
                except json.JSONDecodeError:
                    pass
            
            # Add system participants if mentioned
            for sys_participant in self.system_participants:
                if sys_participant.lower() in text.lower():
                    req_participants.append(sys_participant)
            
            # Extract sequential interactions
            req_messages = self._extract_sequential_messages(text, req_participants, req_id)
            messages.extend(req_messages)
        
        return messages
    
    def _matches_scenario(self, req: Dict[str, Any], scenario: str) -> bool:
        """Check if requirement matches the given scenario."""
        if not scenario:
            return True  # If no scenario specified, include all requirements
        
        text = (req.get('current_text') or req.get('original_text', '')).lower()
        module_name = (req.get('module_name') or '').lower()
        scenario_lower = scenario.lower()
        
        # Check if scenario name is in text or module name
        # Also check if scenario keywords are in the requirement
        scenario_keywords = scenario_lower.split()
        for keyword in scenario_keywords:
            if keyword in text or keyword in module_name:
                return True
        
        # If no match, still include the requirement to avoid filtering everything
        return True
    
    def _extract_sequential_messages(self, text: str, participants: List[str], 
                                    req_id: str) -> List[Dict[str, Any]]:
        """Extract sequential messages from requirement text."""
        messages = []
        text_lower = text.lower()
        
        # Extract action verbs for message content
        action_verbs = ['enter', 'validate', 'grant', 'perform', 'upload', 'download', 'login', 'logout', 
                       'authenticate', 'authorize', 'create', 'update', 'delete', 'read', 'write']
        
        # Check if any action verb is present
        has_action = any(verb in text_lower for verb in action_verbs)
        
        if has_action and len(participants) >= 2:
            # Determine participants based on text content
            from_participant = None
            to_participant = None
            
            # Normalize participant names for comparison
            participants_lower = [p.lower() for p in participants]
            
            # Find which participants are mentioned in the text
            mentioned_participants = []
            for participant in participants:
                if participant.lower() in text_lower:
                    mentioned_participants.append(participant)
            
            # If we have mentioned participants, use them
            if len(mentioned_participants) >= 2:
                from_participant = mentioned_participants[0]
                to_participant = mentioned_participants[1]
            elif len(mentioned_participants) == 1:
                from_participant = mentioned_participants[0]
                # Find the next participant that's not the same
                for p in participants:
                    if p != from_participant:
                        to_participant = p
                        break
            else:
                # Default to first two participants
                from_participant = participants[0]
                to_participant = participants[1] if len(participants) > 1 else participants[0]
            
            # Extract message content
            message_content = self._extract_message_content(text)
            
            if message_content:
                messages.append({
                    'from': from_participant,
                    'to': to_participant,
                    'message': message_content,
                    'type': 'synchronous',
                    'source_req_id': req_id,
                    'step_number': len(messages) + 1
                })
        
        return messages
    
    def _extract_message_content(self, text: str) -> str:
        """Extract message content from text."""
        # Remove modal verbs, common words, and sequential keywords
        text = re.sub(r'\b(?:shall|must|should|will|may|the|a|an)\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(?:first|then|next|after|before|finally|subsequently)\b', '', text, flags=re.IGNORECASE)
        text = text.strip()
        
        # Limit message length
        if len(text) > 50:
            text = text[:47] + '...'
        
        return text.capitalize()
