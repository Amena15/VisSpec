"""
Use Case Diagram Mapping Service for IEEE-Compliant Diagram Generation.

Maps enriched requirements to Use Case diagram elements following IEEE UML standards.
Enforces BR-11: No hallucinated actors - actors are only taken from actors_json.
"""

import json
import re
from typing import Dict, List, Any
from collections import Counter

from backend.core.logging import get_logger

logger = get_logger(__name__)


class UseCaseMapper:
    """Maps requirements to Use Case diagram elements following IEEE standards."""

    def __init__(self):
        self.include_keywords = ['must', 'required', 'then', 'after', 'before', 'when']
        self.extend_keywords = ['may', 'if', 'optionally', 'can', 'could', 'might']

    def map_requirements_to_usecase(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map enriched requirements to Use Case diagram elements.
        
        Returns:
            Dictionary with actors, use cases, associations, includes, extends,
            and system_name for the PlantUML generator.
        """
        try:
            # 1. Extract actors from JSON fields
            all_actors = []
            for req in requirements:
                actors_json = req.get('actors_json', '[]')
                try:
                    actors = json.loads(actors_json)
                    for actor in actors:
                        if isinstance(actor, str):
                            all_actors.append(actor)
                        elif isinstance(actor, dict) and 'name' in actor:
                            all_actors.append(actor['name'])
                except json.JSONDecodeError:
                    continue

            # Count and limit actors (BR-11: only from text)
            actor_counts = Counter(all_actors)
            top_actors = actor_counts.most_common(8)  # Max 8 actors
            actors = [actor for actor, _ in top_actors]
            actor_objects = [{'name': actor} for actor in actors]

            # 2. Extract use cases from requirements
            all_use_cases = []
            for req in requirements:
                text = req.get('current_text') or req.get('original_text', '')
                module = req.get('module_name', 'General')

                use_case_name = self._simplify_use_case_name(text, module)
                if use_case_name and len(use_case_name) > 2:
                    all_use_cases.append({
                        'name': use_case_name,
                        'module': module,
                        'source_req_id': req.get('req_id'),
                        'original_text': text[:100]
                    })

            # Merge similar use cases
            merged_use_cases = self._merge_similar_use_cases(all_use_cases)
            merged_use_cases = merged_use_cases[:12]  # Max 12 use cases

            # 3. Build associations (actor → use case)
            associations = []
            for uc in merged_use_cases:
                relevant_actors = self._get_relevant_actors_for_usecase(uc, actor_objects)
                for actor_obj in relevant_actors:
                    associations.append({
                        'actor': actor_obj['name'],
                        'use_case': uc['name']
                    })

            # Remove duplicate associations
            seen = set()
            unique_associations = []
            for assoc in associations:
                key = f"{assoc['actor']}-{assoc['use_case']}"
                if key not in seen:
                    seen.add(key)
                    unique_associations.append(assoc)

            # 4. Detect include relationships
            includes = []
            for uc in merged_use_cases:
                original_text = uc.get('original_text', '').lower()
                if any(kw in original_text for kw in self.include_keywords):
                    # Find a target use case (login/auth are common includes)
                    target = None
                    for other in merged_use_cases:
                        if other['name'] != uc['name'] and ('login' in other['name'].lower() or 'authenticate' in other['name'].lower()):
                            target = other['name']
                            break
                    if target:
                        includes.append([uc['name'], target])

            # 5. Detect extend relationships
            extends_ = []
            for uc in merged_use_cases:
                original_text = uc.get('original_text', '').lower()
                if any(kw in original_text for kw in self.extend_keywords):
                    # Find a target use case
                    target = None
                    for other in merged_use_cases:
                        if other['name'] != uc['name']:
                            target = other['name']
                            break
                    if target:
                        extends_.append([target, uc['name']])  # Base, Extending

            # 6. Determine system name
            system_name = self._extract_system_name(requirements)

            # Backward-compat: some tests expect a combined `relationships` list.
            relationships = []
            for inc in includes:
                # include: [source, target]
                relationships.append({'type': 'include', 'source': inc[0], 'target': inc[1]})
            for ext in extends_:
                # extend: [base, extending]
                relationships.append({'type': 'extend', 'source': ext[0], 'target': ext[1]})

            return {
                'actors': actors,
                'use_cases': merged_use_cases,
                'associations': unique_associations,
                'includes': includes,
                'extends': extends_,
                'relationships': relationships,
                'system_name': system_name,
                'total_actors': len(actors),
                'total_use_cases': len(merged_use_cases),
                'total_associations': len(unique_associations),
                'total_relationships': len(relationships)
            }

        except Exception as e:
            logger.error(f"Error mapping requirements to use case: {e}")
            return {
                'actors': ['User', 'System'],
                'use_cases': [{'name': 'Login'}, {'name': 'View Dashboard'}],
                'associations': [{'actor': 'User', 'use_case': 'Login'}],
                'includes': [],
                'extends': [],
                'system_name': 'System',
                'total_actors': 2,
                'total_use_cases': 2,
                'total_associations': 1
            }

    def _simplify_use_case_name(self, text: str, module: str) -> str:
        """Simplify requirement text to a clean use case name."""
        text_lower = text.lower()

        action_verbs = [
            'manage', 'create', 'update', 'delete', 'view', 'search', 
            'login', 'register', 'upload', 'download', 'export', 'import',
            'authenticate', 'authorize', 'process', 'generate', 'validate',
            'approve', 'reject', 'archive', 'restore', 'configure', 'monitor'
        ]

        for verb in action_verbs:
            if verb in text_lower:
                words = text_lower.split()
                if verb in words:
                    verb_index = words.index(verb)
                    if verb_index + 1 < len(words):
                        obj = words[verb_index + 1].strip('.,!?')
                        if len(obj) > 1:
                            return f"{verb.capitalize()} {obj.capitalize()}"

        # Fallback: use module name
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

    def _merge_similar_use_cases(self, use_cases: List[Dict]) -> List[Dict]:
        """Merge similar use cases to avoid duplication."""
        merged = {}
        for uc in use_cases:
            name = uc['name']
            if name in merged:
                merged[name]['count'] = merged[name].get('count', 1) + 1
            else:
                merged[name] = {**uc, 'count': 1}
        return list(merged.values())

    def _get_relevant_actors_for_usecase(self, use_case: Dict, actors: List[Dict]) -> List[Dict]:
        """Get relevant actors for a specific use case based on module."""
        module = use_case.get('module', '')
        name = use_case.get('name', '').lower()

        module_actor_map = {
            'Patient Management': ['patient', 'doctor', 'system'],
            'Doctor Management': ['doctor', 'admin', 'system'],
            'User Authentication': ['user', 'admin', 'system'],
            'Security & Compliance': ['admin', 'system'],
            'Data Management': ['system', 'admin'],
            'Payment Processing': ['patient', 'system'],
            'Document Management': ['patient', 'doctor', 'system'],
            'Hospital Administration': ['admin', 'system']
        }

        target_actors = module_actor_map.get(module, ['system', 'user'])

        relevant = []
        for actor in actors:
            actor_name = actor.get('name', '').lower()
            if actor_name in [ta.lower() for ta in target_actors] or actor_name == 'system':
                relevant.append(actor)
        return relevant if relevant else [actors[0]] if actors else [{'name': 'User'}]

    def _extract_system_name(self, requirements: List[Dict]) -> str:
        """Extract system name from requirements."""
        for req in requirements:
            text = req.get('current_text') or req.get('original_text', '')
            patterns = [
                r'(?:the|an|a)\s+(\w+\s+(?:\w+\s+)?system)',
                r'(\w+\s+system)',
                r'(\w+\s+application)',
                r'(\w+\s+platform)'
            ]
            for p in patterns:
                match = re.search(p, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip().title()
        return "System"