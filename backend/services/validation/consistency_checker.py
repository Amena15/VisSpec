"""
Consistency checker for requirements.
Detects contradictions, conflicting terms, and inconsistent terminology.
"""
import re
from typing import List, Dict, Any, Set
from collections import defaultdict

from backend.core.logging import get_logger

logger = get_logger(__name__)

# Contradictory term pairs
CONTRADICTIONS = [
    ("always", "never"),
    ("must", "must not"),
    ("shall", "shall not"),
    ("required", "optional"),
    ("mandatory", "optional"),
    ("enabled", "disabled"),
    ("allow", "prevent"),
    ("permit", "forbid"),
    ("include", "exclude"),
    ("accept", "reject"),
]


class ConsistencyChecker:
    """Checks for contradictions and inconsistencies across requirements."""

    def _matches_term(self, text: str, term: str) -> bool:
        """Match a contradiction term as a whole phrase, not a substring."""
        return bool(re.search(r"\b" + re.escape(term) + r"\b", text))

    def check_single(self, text: str) -> List[Dict[str, Any]]:
        """Check a single requirement text for internal contradictions."""
        defects = []
        lower_text = text.lower()

        for term_a, term_b in CONTRADICTIONS:
            if self._matches_term(lower_text, term_a) and self._matches_term(lower_text, term_b):
                # Per FYP Report specification: contradiction confidence = 0.90
                confidence = 0.90
                defects.append({
                    "text": text,
                    "type": "inconsistency",
                    "severity": "high",
                    "confidence": confidence,
                    "description": f"Contradictory terms '{term_a}' and '{term_b}' found in the same requirement.",
                    "suggestion": f"Resolve the contradiction between '{term_a}' and '{term_b}'.",
                })

        return defects

    def check_multiple(self, requirements: List[str]) -> List[Dict[str, Any]]:
        """
        Enhanced cross-requirement consistency check (Phase 2.3).
        Uses TF-IDF similarity and advanced contradiction detection.
        """
        defects = []

        # Extract key entities and their stated behaviors
        entity_behaviors: Dict[str, Set[str]] = defaultdict(set)
        requirement_index = {}  # Map requirement text to its index

        for idx, req_text in enumerate(requirements):
            requirement_index[req_text] = idx
            
            # Enhanced extraction: look for more patterns
            patterns = [
                r"(?:the\s+)?(?:system|user|application|admin|patient|doctor)\s+(?:shall|should|must|will|may)\s+(.+?)(?:\.|$)",
                r"(?:the\s+)?(\w+)\s+(?:shall|should|must|will|may)\s+(.+?)(?:\.|$)",
                r"(\w+)\s+(?:shall|should|must|will|may)\s+(.+?)(?:\.|$)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, req_text, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 2:
                        entity, behavior = match.groups()
                    else:
                        behavior = match.group(1).strip()
                        entity_match = re.search(r"(?:the\s+)?(\w+)", req_text, re.IGNORECASE)
                        entity = entity_match.group(1).lower() if entity_match else "system"
                    
                    entity = entity.lower()
                    behavior = behavior.strip().lower()
                    entity_behaviors[entity].add((behavior, idx))  # Store with index
                    break

        # 1. Check for direct contradictory behaviors
        for entity, behaviors in entity_behaviors.items():
            behavior_list = list(behaviors)
            for i, (b1, idx1) in enumerate(behavior_list):
                for j, (b2, idx2) in enumerate(behavior_list[i + 1:], i + 1):
                    for term_a, term_b in CONTRADICTIONS:
                        if self._matches_term(b1, term_a) and self._matches_term(b2, term_b):
                            confidence = 0.90
                            defects.append({
                                "text": f"Requirements about '{entity}' (req {idx1+1} and req {idx2+1})",
                                "type": "inconsistency",
                                "severity": "high",
                                "confidence": confidence,
                                "description": f"Contradictory behaviors for '{entity}': '{b1}' vs '{b2}'.",
                                "suggestion": f"Reconcile the conflicting requirements for '{entity}'.",
                                "req_indices": [idx1, idx2]
                            })
                        elif self._matches_term(b1, term_b) and self._matches_term(b2, term_a):
                            confidence = 0.90
                            defects.append({
                                "text": f"Requirements about '{entity}' (req {idx1+1} and req {idx2+1})",
                                "type": "inconsistency",
                                "severity": "high",
                                "confidence": confidence,
                                "description": f"Contradictory behaviors for '{entity}': '{b1}' vs '{b2}'.",
                                "suggestion": f"Reconcile the conflicting requirements for '{entity}'.",
                                "req_indices": [idx1, idx2]
                            })

        # 2. Advanced similarity-based inconsistency detection
        similarity_defects = self._check_similarity_inconsistencies(requirements, requirement_index)
        defects.extend(similarity_defects)

        # 3. Cross-requirement terminology consistency
        terminology_defects = self._check_terminology_consistency(requirements)
        defects.extend(terminology_defects)

        return defects

    def _check_similarity_inconsistencies(self, requirements: List[str], requirement_index: Dict[str, int]) -> List[Dict[str, Any]]:
        """Check for inconsistencies using TF-IDF similarity analysis."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np

            defects = []

            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            try:
                tfidf_matrix = vectorizer.fit_transform(requirements)
                similarity_matrix = cosine_similarity(tfidf_matrix)
            except Exception as e:
                logger.debug(f"TF-IDF analysis failed: {e}")
                return []

            # Find similar but potentially contradictory requirements
            for i in range(len(requirements)):
                for j in range(i + 1, len(requirements)):
                    similarity = similarity_matrix[i][j]
                    
                    # Only check high-similarity pairs (>0.7)
                    if similarity > 0.7:
                        req1 = requirements[i].lower()
                        req2 = requirements[j].lower()
                        
                        # Check for contradictory terms in similar requirements
                        contradiction_found = False
                        for term_a, term_b in CONTRADICTIONS:
                            if term_a in req1 and term_b in req2:
                                contradiction_found = True
                                break
                            elif term_b in req1 and term_a in req2:
                                contradiction_found = True
                                break
                        
                        if contradiction_found:
                            confidence = min(0.85, similarity + 0.1)  # Higher confidence for similar + contradictory
                            defects.append({
                                "text": f"Similar contradictory requirements (req {i+1} and req {j+1})",
                                "type": "inconsistency",
                                "severity": "high",
                                "confidence": confidence,
                                "description": f"Requirements {i+1} and {j+1} are {similarity:.2f} similar but contain contradictory terms.",
                                "suggestion": "Review and resolve the contradiction between these similar requirements.",
                                "req_indices": [i, j],
                                "similarity": float(similarity)
                            })

            return defects

        except ImportError:
            logger.warning("scikit-learn not available for similarity analysis")
            return []
        except Exception as e:
            logger.error(f"Similarity analysis failed: {e}")
            return []

    def _check_terminology_consistency(self, requirements: List[str]) -> List[Dict[str, Any]]:
        """Check for inconsistent terminology across requirements."""
        defects = []
        
        # Extract key terms and their contexts
        term_usage = {}
        
        for idx, req in enumerate(requirements):
            # Look for important terms (actors, actions, objects)
            terms = re.findall(r'\b(?:system|user|admin|patient|doctor|data|file|database|interface|application)\b', req, re.IGNORECASE)
            
            for term in terms:
                term_lower = term.lower()
                if term_lower not in term_usage:
                    term_usage[term_lower] = []
                term_usage[term_lower].append({
                    'index': idx,
                    'context': req,
                    'case': term  # Preserve original case
                })
        
        # Check for case inconsistencies
        for term, usages in term_usage.items():
            if len(usages) > 1:
                cases = set(usage['case'] for usage in usages)
                if len(cases) > 1:
                    # Found case inconsistency
                    confidence = 0.75
                    indices = [usage['index'] for usage in usages]
                    
                    defects.append({
                        "text": f"Inconsistent terminology for '{term}'",
                        "type": "inconsistency",
                        "severity": "medium",
                        "confidence": confidence,
                        "description": f"The term '{term}' is used with different capitalization: {', '.join(sorted(cases))}",
                        "suggestion": f"Use consistent capitalization for '{term}' across all requirements.",
                        "req_indices": indices,
                        "term_variations": list(cases)
                    })

        return defects
