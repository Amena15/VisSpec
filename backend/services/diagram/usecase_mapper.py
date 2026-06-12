"""
Use Case Diagram Mapping Service for IEEE-Compliant Diagram Generation.

Maps enriched requirements to Use Case diagram elements following IEEE UML standards.
Enforces BR-11: No hallucinated actors - actors are only taken from actors_json.
Simplified for cleaner, professional diagrams with limited clutter.
"""

import json
import re
from typing import Dict, List, Any
from collections import Counter

from backend.core.logging import get_logger

logger = get_logger(__name__)


class UseCaseMapper:
    """Maps requirements to Use Case diagram elements with simplified, clean output."""
    
    def __init__(self):
        self.include_keywords = ['must', 'required', 'then', 'after', 'before', 'when']
        self.extend_keywords = ['may', 'if', 'optionally', 'can', 'could', 'might']
    
    def map_requirements_to_usecase(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map enriched requirements to Use Case diagram elements.
        
        Args:
            requirements: List of enriched requirement dictionaries
            
        Returns:
            Dictionary with actors, use cases, and relationships (simplified and clean)
        """
        try:
            # Extract and consolidate actors - limit to top 6 most frequent
            all_actors = []
            for req in requirements:
                actors_json = req.get('actors_json', '[]')
                try:
                    actors = json.loads(actors_json)
                    # Handle both string lists and dict lists
                    for actor in actors:
                        if isinstance(actor, str):
                            all_actors.append(actor)
                        elif isinstance(actor, dict) and 'name' in actor:
                            all_actors.append(actor['name'])
                except json.JSONDecodeError:
                    continue
            
            # Count actor frequency and limit to top 6
            actor_counts = Counter(all_actors)
            top_actors = actor_counts.most_common(6)
            actors = [{'name': actor, 'count': count} for actor, count in top_actors]
            
            # Extract and consolidate use cases - limit to top 10
            all_use_cases = []
            for req in requirements:
                text = req.get('current_text') or req.get('original_text', '')
                module = req.get('module_name', 'General')
                
                # Create simplified use case name
                use_case_name = self._simplify_use_case_name(text, module)
                if use_case_name:
                    all_use_cases.append({
                        'name': use_case_name,
                        'module': module,
                        'requirement_id': req.get('req_id'),
                        'source_req_id': req.get('req_id'),  # For traceability
                        'original_text': text[:100]
                    })
            
            # Merge similar use cases
            merged_use_cases = self._merge_similar_use_cases(all_use_cases)
            
            # Limit to top 10 use cases
            merged_use_cases = merged_use_cases[:10]
            
            # Create clean associations
            associations = []
            for uc in merged_use_cases:
                relevant_actors = self._get_relevant_actors_for_usecase(uc, actors)
                for actor in relevant_actors:
                    associations.append({
                        'actor': actor['name'],
                        'use_case': uc['name']
                    })
            
            # Remove duplicate associations
            associations = list({f"{a['actor']}-{a['use_case']}": a for a in associations}.values())
            
            # Add simplified include/extend relationships
            for uc in merged_use_cases:
                if 'login' in uc['name'].lower() or 'authenticate' in uc['name'].lower():
                    uc['included_by'] = []
                    for other_uc in merged_use_cases:
                        if other_uc != uc and 'profile' in other_uc['name'].lower():
                            uc['included_by'].append(other_uc['name'])
            
            # Create relationships for test compatibility
            relationships = []
            for assoc in associations:
                relationships.append({
                    'type': 'association',
                    'source': assoc['actor'],
                    'target': assoc['use_case']
                })
            
            # Add include relationships where applicable
            for uc in merged_use_cases:
                # Check for include keywords in requirement text
                original_text = uc.get('original_text', '').lower()
                if any(keyword in original_text for keyword in self.include_keywords):
                    # Find login use case to include
                    login_uc = next((other_uc for other_uc in merged_use_cases 
                                    if 'login' in other_uc['name'].lower() or 'authenticate' in other_uc['name'].lower()), None)
                    if login_uc and login_uc != uc:
                        relationships.append({
                            'type': 'include',
                            'source': uc['name'],
                            'target': login_uc['name']
                        })
                
                # Check for "before" keyword indicating include relationship
                if 'before' in original_text:
                    # Find use case that comes after "before"
                    parts = original_text.split('before')
                    if len(parts) > 1:
                        after_text = parts[1].strip()
                        # Find matching use case
                        target_uc = next((other_uc for other_uc in merged_use_cases 
                                        if other_uc != uc and any(word in other_uc['name'].lower() for word in after_text.split()[:3])), None)
                        if target_uc:
                            relationships.append({
                                'type': 'include',
                                'source': uc['name'],
                                'target': target_uc['name']
                            })
                
                # Existing included_by logic
                if 'included_by' in uc and uc['included_by']:
                    for included_by in uc['included_by']:
                        relationships.append({
                            'type': 'include',
                            'source': uc['name'],
                            'target': included_by
                        })
            
            return {
                'actors': actors,
                'actor_names': [actor['name'] for actor in actors],  # Simple list for BR-11 compliance
                'use_cases': merged_use_cases,
                'associations': associations,
                'relationships': relationships,
                'total_actors': len(actors),
                'total_use_cases': len(merged_use_cases),
                'total_associations': len(associations)
            }
            
        except Exception as e:
            logger.error(f"Error mapping requirements to use case: {e}")
            return {
                'actors': [],
                'use_cases': [],
                'associations': [],
                'relationships': [],
                'total_actors': 0,
                'total_use_cases': 0,
                'total_associations': 0
            }
    
    def _simplify_use_case_name(self, text: str, module: str) -> str:
        """Simplify requirement text to a clean use case name."""
        text_lower = text.lower()
        
        # Extract main action verb
        action_verbs = ['manage', 'create', 'update', 'delete', 'view', 'search', 'login', 'register', 
                        'upload', 'download', 'export', 'import', 'authenticate', 'authorize', 'process',
                        'generate', 'validate', 'approve', 'reject', 'archive', 'restore']
        
        for verb in action_verbs:
            if verb in text_lower:
                words = text_lower.split()
                if verb in words:
                    verb_index = words.index(verb)
                    if verb_index + 1 < len(words):
                        object_word = words[verb_index + 1]
                        object_word = object_word.strip('.,!?')
                        return f"{verb.capitalize()} {object_word.capitalize()}"
        
        # Fallback to module-based naming
        module_map = {
            'User Authentication': 'User Login',
            'Patient Management': 'Manage Patient',
            'Doctor Management': 'Manage Doctor',
            'Hospital Administration': 'Administer Hospital',
            'Security & Compliance': 'Ensure Security',
            'Data Management': 'Manage Data',
            'Payment Processing': 'Process Payment',
            'Document Management': 'Manage Document',
            'Reporting & Analytics': 'View Reports',
            'External Integration': 'Integrate External',
            'Government Compliance': 'Ensure Compliance',
            'Elderly Care': 'Care for Elderly'
        }
        
        return module_map.get(module, f"{module} Operation")
    
    def _merge_similar_use_cases(self, use_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge similar use cases to avoid duplication."""
        merged = {}
        
        for uc in use_cases:
            name = uc['name']
            if name in merged:
                merged[name]['count'] = merged[name].get('count', 1) + 1
            else:
                merged[name] = {**uc, 'count': 1}
        
        return list(merged.values())
    
    def _get_relevant_actors_for_usecase(self, use_case: Dict[str, Any], actors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get relevant actors for a specific use case based on module."""
        module = use_case.get('module', '')
        name = use_case.get('name', '')
        if isinstance(name, str):
            name = name.lower()
        
        relevant_actors = []
        
        # Always include System
        for a in actors:
            actor_name = a.get('name', '')
            if isinstance(actor_name, str) and actor_name.lower() == 'system':
                relevant_actors.append(a)
                break
        
        # Module-specific actor associations
        module_actor_map = {
            'Patient Management': ['patient', 'doctor', 'system'],
            'Doctor Management': ['doctor', 'admin', 'system'],
            'User Authentication': ['user', 'admin', 'system'],
            'Security & Compliance': ['admin', 'system'],
            'Data Management': ['system', 'admin'],
            'Payment Processing': ['patient', 'system', 'hospital'],
            'Document Management': ['patient', 'doctor', 'system'],
            'Hospital Administration': ['admin', 'system']
        }
        
        target_actors = module_actor_map.get(module, ['system'])
        
        for actor in actors:
            actor_name = actor.get('name', '')
            if isinstance(actor_name, str):
                if actor_name.lower() in [ta.lower() for ta in target_actors]:
                    if actor not in relevant_actors:
                        relevant_actors.append(actor)
        
        return relevant_actors
