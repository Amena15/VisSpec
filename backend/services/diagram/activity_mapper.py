"""
Activity Diagram Mapping Service for IEEE-Compliant Diagram Generation.

Maps enriched requirements to Activity diagram elements following IEEE UML standards.
"""

import json
import re
from typing import Dict, List, Any, Set
from collections import defaultdict

from backend.core.logging import get_logger

logger = get_logger(__name__)


class ActivityMapper:
    """Maps requirements to Activity diagram elements."""
    
    def __init__(self):
        self.decision_keywords = ['if', 'else', 'otherwise', 'when', 'unless', 'condition']
        self.action_keywords = ['shall', 'must', 'will', 'should', 'perform', 'execute', 'process']
    
    def map_requirements_to_activity(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map enriched requirements to Activity diagram elements.
        
        Args:
            requirements: List of enriched requirement dictionaries
            
        Returns:
            Dictionary with activities, decisions, and control flow
        """
        # Extract activities from functional requirements
        activities = self._extract_activities(requirements)
        
        # Extract decision nodes from conditional requirements
        decisions = self._extract_decisions(requirements)
        
        # Extract control flow based on sequence_order
        control_flow = self._extract_control_flow(requirements, activities)
        
        return {
            'activities': activities,
            'decisions': decisions,
            'control_flow': control_flow,
            'start_node': 'Start',
            'end_node': 'End'
        }
    
    def _extract_activities(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract activities from functional requirements."""
        activities = []
        activity_names = set()
        
        for req in requirements:
            category = req.get('category', '').lower()
            if category != 'functional':
                continue
            
            text = req.get('current_text') or req.get('original_text', '')
            req_id = req.get('req_id')
            semantic_id = req.get('semantic_id')
            sequence_order = req.get('sequence_order', 0)
            
            # Extract action phrases
            action_phrases = self._extract_action_phrases(text)
            
            for phrase in action_phrases:
                activity_name = self._format_activity_name(phrase)
                
                if activity_name not in activity_names:
                    activity_names.add(activity_name)
                    activities.append({
                        'name': activity_name,
                        'source_req_id': req_id,
                        'semantic_id': semantic_id,
                        'sequence_order': sequence_order,
                        'original_text': text
                    })
        
        # Sort by sequence_order
        activities.sort(key=lambda x: x['sequence_order'])
        return activities
    
    def _extract_action_phrases(self, text: str) -> List[str]:
        """Extract action phrases from requirement text."""
        phrases = []
        
        # Common action verbs
        action_verbs = [
            'allow', 'enable', 'provide', 'support', 'permit', 'facilitate',
            'require', 'create', 'update', 'delete', 'read', 'view', 'list', 'search',
            'upload', 'download', 'export', 'import', 'generate', 'process',
            'validate', 'verify', 'authenticate', 'authorize', 'login', 'logout',
            'manage', 'administer', 'configure', 'monitor', 'track', 'log',
            'send', 'receive', 'store', 'retrieve', 'display', 'show'
        ]
        
        text_lower = text.lower()
        
        for verb in action_verbs:
            if verb in text_lower:
                # Extract the phrase containing the verb
                pattern = rf'\w+\s+{verb}\s+\w+(?:\s+\w+)*'
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    # Clean up the phrase
                    phrase = match.strip()
                    if len(phrase) > 5:
                        phrases.append(phrase)
        
        return phrases
    
    def _format_activity_name(self, phrase: str) -> str:
        """Format action phrase as activity name."""
        # Remove common words and capitalize
        phrase = re.sub(r'\b(?:the|a|an|to|for|with|by|from|in|on|at)\b', '', phrase, flags=re.IGNORECASE)
        phrase = phrase.strip()
        return ' '.join(word.capitalize() for word in phrase.split())
    
    def _extract_decisions(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract decision nodes from conditional requirements."""
        decisions = []
        
        for req in requirements:
            text = req.get('current_text') or req.get('original_text', '')
            text_lower = text.lower()
            req_id = req.get('req_id')
            
            # Check for decision keywords
            has_decision = any(keyword in text_lower for keyword in self.decision_keywords)
            
            if has_decision:
                # Extract condition
                condition = self._extract_condition(text)
                
                if condition:
                    decisions.append({
                        'name': condition,
                        'source_req_id': req_id,
                        'original_text': text
                    })
        
        return decisions
    
    def _extract_condition(self, text: str) -> str:
        """Extract condition from text."""
        # Look for patterns like "if X then Y" or "when X"
        patterns = [
            r'if\s+(.+?)\s+then',
            r'when\s+(.+?)(?:\s+then|\s+,|\.$)',
            r'unless\s+(.+?)(?:\s+then|\s+,|\.$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                condition = match.group(1).strip()
                # Limit condition length
                if len(condition) > 30:
                    condition = condition[:27] + '...'
                return condition.capitalize()
        
        return ''
    
    def _extract_control_flow(self, requirements: List[Dict[str, Any]], 
                              activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract control flow based on sequence_order."""
        control_flow = []
        
        # Sort activities by sequence_order
        sorted_activities = sorted(activities, key=lambda x: x['sequence_order'])
        
        # Create flow between consecutive activities
        for i in range(len(sorted_activities) - 1):
            control_flow.append({
                'from': sorted_activities[i]['name'],
                'to': sorted_activities[i + 1]['name'],
                'type': 'flow'
            })
        
        return control_flow
