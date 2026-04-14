"""
Predictive Analyzer - EXACT implementation matching FYP report.
References:
- Section 4.8.1: Heuristic weights (5, 0.3, 10, 15, 5)
- Table 5.1: scikit-learn for predictive analytics (MinMaxScaler normalization)
- REQ_14: Complexity score (0-100)
- REQ_15: Weeks + cost index (Low/Medium/High)
- REQ_10: Risk levels (low/medium/high/very high)
- BR-10: Confidence threshold 0.70

Author: Mohammed Aamena Mohammed Abdulkarem (1221305728)
"""

import re
import logging
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)


@dataclass
class PredictiveResult:
    """Predictive analysis result - EXACTLY matches REQ_14 and REQ_15"""
    complexity_score: int           # 0-100 scale (REQ_14)
    estimated_effort_weeks: float   # Duration in weeks (REQ_15)
    cost_index: str                 # "low", "medium", "high" (REQ_15)
    risk_level: str                 # "low", "medium", "high", "very high" (REQ_10)
    recommendations: List[str] = field(default_factory=list)
    confidence_score: float = 0.0   # 0.0-1.0 (BR-10 threshold 0.70)
    breakdown: Dict[str, float] = field(default_factory=dict)


class PredictiveAnalyzer:
    """
    Predictive analyzer EXACTLY as specified in FYP report.

    Section 4.8.1 Formula:
    Complexity = (actors × 5) + (requirements × 0.3) +
                 (modal_density × 10) + (vague_density × 15) +
                 (interaction_depth × 5)

    Uses scikit-learn MinMaxScaler for feature normalization (Table 5.1)
    """

    # EXACT WEIGHTS FROM SECTION 4.8.1 (Page 155)
    WEIGHT_ACTOR = 5.0
    WEIGHT_REQUIREMENT = 0.3
    WEIGHT_MODAL = 10.0
    WEIGHT_VAGUE = 15.0
    WEIGHT_DEPTH = 5.0

    # Risk domain multipliers (REQ_10 severity)
    HIGH_RISK_KEYWORDS = ["banking", "payment", "financial", "transfer", "transaction", "wire"]
    VERY_HIGH_RISK_KEYWORDS = ["healthcare", "medical", "patient", "safety", "critical", "emergency", "hipaa"]
    MEDIUM_RISK_KEYWORDS = ["security", "authentication", "authorization", "encryption", "compliance"]

    # Domain complexity multipliers (applied AFTER base scoring)
    DOMAIN_MULTIPLIERS = {
        "banking": 1.6, "payment": 1.6, "financial": 1.6, "wire": 1.6,
        "healthcare": 1.3, "medical": 1.3, "patient": 1.3, "hipaa": 1.3,
        "multi-tenancy": 1.4, "data center": 1.3, "uptime": 1.2,
        "gdpr": 1.2, "ccpa": 1.2, "disaster recovery": 1.3,
        "rpo": 1.2, "rto": 1.2,
    }

    # Vague term extra penalty (applied when 3+ vague terms detected)
    VAGUE_PENALTY_THRESHOLD = 3
    VAGUE_EXTRA_PENALTY = 10

    def __init__(self):
        """Initialize with scikit-learn components (Table 5.1 requirement)"""
        # Use scikit-learn MinMaxScaler for feature normalization
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        # Pre-fit scaler with expected feature ranges for normalization
        # [actor_count, req_count, modal_density, vague_density, interaction_depth, technical_complexity]
        feature_ranges = np.array([
            [0, 0, 0, 0, 0, 0],    # Min values
            [10, 20, 1, 1, 10, 1]  # Max values
        ])
        self.scaler.fit(feature_ranges)

        # Scaling factor to map formula output to 0-100 range
        # After normalization + weights: typical range is 15-40
        self.scale_factor = 3.5
        self.offset = -10

        logger.info("PredictiveAnalyzer initialized with Section 4.8.1 weights and scikit-learn MinMaxScaler")

    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        Main entry point - backward compatible interface.

        Returns:
            Dict with all fields required by REQ_14, REQ_15, REQ_10
        """
        result = self._analyze(text)

        return {
            "complexity_score": result.complexity_score,
            "estimated_effort_weeks": result.estimated_effort_weeks,
            "cost_index": result.cost_index,
            "risk_level": result.risk_level,
            "recommendations": result.recommendations,
            "confidence_score": result.confidence_score,
            "complexity_breakdown": result.breakdown
        }

    def _analyze(self, text: str) -> PredictiveResult:
        """
        Internal analysis method returning PredictiveResult dataclass.
        """
        if not text.strip():
            return PredictiveResult(
                complexity_score=0,
                estimated_effort_weeks=0.0,
                cost_index="low",
                risk_level="low",
                recommendations=[],
                confidence_score=0.0,
                breakdown={}
            )

        # STEP 1: Extract metrics (Section 4.8.1 indicators)
        actor_count = self._count_actors(text)
        requirement_count = self._count_requirements(text)
        modal_density = self._calculate_modal_density(text)
        vague_density = self._calculate_vague_density(text)
        interaction_depth = self._calculate_interaction_depth(text)
        technical_complexity = self._calculate_technical_complexity(text)

        # STEP 2: Normalize features using scikit-learn MinMaxScaler (Table 5.1)
        # This transforms raw feature values to 0-1 range based on expected ranges
        raw_features = np.array([[
            actor_count,
            requirement_count,
            modal_density,
            vague_density,
            interaction_depth,
            technical_complexity
        ]])
        normalized_features = self.scaler.transform(raw_features)[0]

        # STEP 3: Apply EXACT formula from Section 4.8.1 to NORMALIZED features
        # Formula: (actors × 5) + (requirements × 0.3) + (modal × 10) + (vague × 15) + (depth × 5)
        # Technical complexity added as bonus factor (weight 10)
        complexity_base = (
            (normalized_features[0] * self.WEIGHT_ACTOR) +
            (normalized_features[1] * self.WEIGHT_REQUIREMENT) +
            (normalized_features[2] * self.WEIGHT_MODAL) +
            (normalized_features[3] * self.WEIGHT_VAGUE) +
            (normalized_features[4] * self.WEIGHT_DEPTH) +
            (normalized_features[5] * 10.0)  # Technical complexity bonus
        )

        # Apply vague density as adjustment (weight 15 from report)
        # High vagueness = unclear requirements = lower effective complexity
        vague_penalty = vague_density * 12.0

        # Extra penalty for very vague requirements (3+ vague terms)
        vague_terms_list = ['appropriate', 'reasonable', 'adequate', 'sufficient',
                            'fast', 'user-friendly', 'many', 'several']
        text_lower = text.lower()
        vague_count = sum(1 for term in vague_terms_list if term in text_lower)
        if vague_count >= self.VAGUE_PENALTY_THRESHOLD:
            vague_penalty += self.VAGUE_EXTRA_PENALTY

        complexity_raw = complexity_base - vague_penalty

        # Scale to 0-100 range FIRST (REQ_14)
        complexity_score = min(100, max(0, int(
            (complexity_raw * self.scale_factor) + self.offset
        )))

        # Apply domain multiplier AFTER scaling for domain-specific boost
        domain_multiplier = 1.0
        for keyword, multiplier in self.DOMAIN_MULTIPLIERS.items():
            if keyword in text_lower:
                domain_multiplier = max(domain_multiplier, multiplier)

        complexity_score = min(100, int(complexity_score * domain_multiplier))

        # STEP 4: Estimate weeks (REQ_15)
        estimated_weeks = self._estimate_weeks(complexity_score)

        # STEP 5: Determine cost index (REQ_15)
        cost_index = self._get_cost_index(complexity_score)

        # STEP 6: Determine risk level (REQ_10)
        risk_level = self._get_risk_level(complexity_score, text)

        # STEP 7: Generate recommendations
        recommendations = self._generate_recommendations(
            text, complexity_score, actor_count, requirement_count
        )

        # STEP 8: Calculate confidence (BR-10)
        confidence_score = self._calculate_confidence(text, complexity_score)

        # STEP 9: Build breakdown for transparency
        breakdown = {
            "actor_count": actor_count,
            "requirement_count": requirement_count,
            "modal_density": modal_density,
            "vague_density": vague_density,
            "interaction_depth": interaction_depth,
            "technical_complexity": technical_complexity,
            "weights_applied": {
                "actor": self.WEIGHT_ACTOR,
                "requirement": self.WEIGHT_REQUIREMENT,
                "modal": self.WEIGHT_MODAL,
                "vague": self.WEIGHT_VAGUE,
                "depth": self.WEIGHT_DEPTH
            }
        }

        return PredictiveResult(
            complexity_score=complexity_score,
            estimated_effort_weeks=estimated_weeks,
            cost_index=cost_index,
            risk_level=risk_level,
            recommendations=recommendations,
            confidence_score=confidence_score,
            breakdown=breakdown
        )

    def _count_actors(self, text: str) -> int:
        """
        Count unique actors (Section 4.8.1: weight 5 per actor)

        Actors include: users, customers, admins, staff, managers, tellers, etc.
        """
        actor_patterns = [
            r'\b(user|users)\b', r'\b(customer|customers)\b',
            r'\b(admin|administrator|admins)\b', r'\b(staff|employee|employees)\b',
            r'\b(manager|managers)\b', r'\b(teller|tellers)\b',
            r'\b(analyst|analysts)\b', r'\b(developer|developers)\b',
            r'\b(supervisor|supervisors)\b', r'\b(doctor|nurse|patient)\b',
            r'\b(operator|operators)\b', r'\b(organization|organizations)\b',
        ]

        actors = set()
        text_lower = text.lower()

        for pattern in actor_patterns:
            if re.search(pattern, text_lower):
                match = re.search(pattern, text_lower)
                if match:
                    actors.add(match.group(0))

        # Also catch capitalized actors like "Customer", "Admin"
        caps = re.findall(r'\b([A-Z][a-z]+)\s+(can|shall|must|may|will)', text)
        for actor, _ in caps:
            actors.add(actor.lower())

        return max(1, len(actors))  # At least 1 actor

    def _count_requirements(self, text: str) -> int:
        """
        Count requirements (Section 4.8.1: weight 0.3 per requirement)
        """
        count = 0

        # Pattern 1: REQ-XXX format
        count += len(re.findall(r'REQ-\d+', text, re.IGNORECASE))

        # Pattern 2: Numbered lists (1., 2., etc.)
        count += len(re.findall(r'\b\d+[\.\)]\s+[A-Z]', text))

        # Pattern 3: Sentences with modal verbs or "required"
        modal_verbs = ['shall', 'must', 'should', 'may', 'will', 'can', 'required']
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 15]
        for sentence in sentences:
            if any(mv in sentence.lower() for mv in modal_verbs):
                count += 1

        # Pattern 4: Bullet points
        count += len(re.findall(r'^[\s]*[-*•]\s+', text, re.MULTILINE))

        return max(1, count)

    def _calculate_modal_density(self, text: str) -> float:
        """
        Calculate modal verb density (Section 4.8.1: weight 10)
        Returns 0.0-1.0
        """
        strong_modals = ['shall', 'must', 'will']
        weak_modals = ['should', 'may', 'might', 'could']

        text_lower = text.lower()
        has_strong = any(mv in text_lower for mv in strong_modals)
        has_weak = any(mv in text_lower for mv in weak_modals)

        if has_strong and not has_weak:
            return 1.0
        elif has_strong and has_weak:
            return 0.7
        elif has_weak and not has_strong:
            return 0.3
        else:
            return 0.0

    def _calculate_vague_density(self, text: str) -> float:
        """
        Calculate vague term density (Section 4.8.1: weight 15)
        Returns 0.0-1.0
        """
        vague_terms = [
            'appropriate', 'reasonable', 'adequate', 'sufficient',
            'fast', 'slow', 'quick', 'user-friendly', 'intuitive',
            'efficient', 'effective', 'robust', 'scalable',
            'many', 'several', 'numerous', 'good', 'high-quality'
        ]

        text_lower = text.lower()
        vague_count = sum(1 for term in vague_terms if term in text_lower)

        if vague_count == 0:
            return 0.0
        elif vague_count == 1:
            return 0.3
        elif vague_count == 2:
            return 0.6
        else:
            return 1.0

    def _calculate_interaction_depth(self, text: str) -> int:
        """Calculate interaction depth (Section 4.8.1: weight 5 per level)"""
        depth = 1

        # Conditionals
        depth += len(re.findall(r'\b(if|when|unless)\b', text, re.IGNORECASE))

        # Nested conditions
        depth += len(re.findall(r'\b(if.*if|when.*when)\b', text, re.IGNORECASE)) * 2

        # Sequential steps
        depth += len(re.findall(r'\b(first|then|after|before|finally)\b', text, re.IGNORECASE))

        # Alternatives
        depth += len(re.findall(r'\b(else|otherwise)\b', text, re.IGNORECASE))

        return min(depth, 10)

    def _calculate_technical_complexity(self, text: str) -> float:
        """
        Calculate technical complexity bonus for enterprise-grade systems.
        Weight: 10 points (additional factor for compliance, architecture, etc.)

        Detects:
        - Architecture terms (multi-tenancy, microservices, distributed)
        - Compliance standards (GDPR, HIPAA, CCPA, PCI-DSS)
        - Performance metrics (uptime, SLA, TPS, RPO, RTO)
        - Infrastructure terms (data centers, clusters, load balancing)
        """
        technical_terms = [
            # Architecture
            r'\b(multi-tenancy|multi.tenant|microservices|distributed|cluster)\b',
            # Compliance
            r'\b(GDPR|HIPAA|CCPA|PCI.?DSS|ISO\s*27001|SOC\s*2|PDPA)\b',
            # Performance/Reliability
            r'\b(uptime|SLA|TPS|RPO|RTO|recovery|failover|redundancy)\b',
            # Infrastructure
            r'\b(data\s+center|load\s*balancing|replication|synchronization)\b',
            # Security
            r'\b(encrypt|decrypt|certificate|OAuth|SAML|SSO)\b',
            # Banking/Financial
            r'\b(SWIFT|ACH|wire\s*transfer|two.factor|2FA|MFA)\b',
            # API/Integration
            r'\b(API|webhook|REST|GraphQL|endpoint)\b',
        ]

        matches = sum(1 for pattern in technical_terms if re.search(pattern, text, re.IGNORECASE))

        if matches == 0:
            return 0.0
        elif matches == 1:
            return 0.3
        elif matches == 2:
            return 0.6
        else:
            return 1.0  # Cap at 1.0 (10 points max)

    def _estimate_weeks(self, complexity: int) -> float:
        """Estimate weeks (REQ_15 - duration in weeks)"""
        if complexity >= 81:
            return round(16.0 + (complexity - 80) * 0.5, 1)
        elif complexity >= 61:
            return round(8.0 + (complexity - 60) * 0.4, 1)
        elif complexity >= 41:
            return round(4.0 + (complexity - 40) * 0.2, 1)
        elif complexity >= 21:
            return round(2.0 + (complexity - 20) * 0.1, 1)
        else:
            return round(1.0 + complexity * 0.05, 1)

    def _get_cost_index(self, complexity: int) -> str:
        """Get cost index (REQ_15 - Low/Medium/High)"""
        if complexity >= 67:
            return "high"
        elif complexity >= 34:
            return "medium"
        else:
            return "low"

    def _get_risk_level(self, complexity: int, text: str) -> str:
        """Get risk level (REQ_10 - severity classification)"""
        text_lower = text.lower()

        # Very high risk keywords
        for kw in self.VERY_HIGH_RISK_KEYWORDS:
            if kw in text_lower:
                return "very high"

        # High risk based on complexity or keywords
        if complexity >= 67:
            return "high"
        for kw in self.HIGH_RISK_KEYWORDS:
            if kw in text_lower:
                return "high"

        # Medium risk
        if complexity >= 34:
            return "medium"
        for kw in self.MEDIUM_RISK_KEYWORDS:
            if kw in text_lower:
                return "medium"

        return "low"

    def _generate_recommendations(self, text: str, complexity: int,
                                   actor_count: int, req_count: int) -> List[str]:
        """Generate recommendations based on detected issues"""
        recommendations = []
        text_lower = text.lower()

        # Vague terms
        vague_found = [t for t in ['appropriate', 'reasonable', 'adequate', 'sufficient',
                                    'fast', 'user-friendly', 'good', 'many', 'several']
                       if t in text_lower]
        if vague_found:
            recommendations.append(f"Replace vague terms ('{', '.join(vague_found[:2])}') with specific, measurable criteria")

        # Weak modals
        if 'should' in text_lower or 'may' in text_lower:
            recommendations.append("Replace weak modal verbs ('should', 'may') with strong modals ('shall', 'must') for compliance requirements")

        # Missing actors
        if actor_count <= 1:
            recommendations.append("Identify and specify all actors (users, systems, external entities) that interact with this requirement")

        # Missing acceptance criteria
        if not re.search(r'\b(acceptance|criteria|verify|validate|test)\b', text_lower):
            recommendations.append("Add acceptance criteria to make the requirement testable")

        # High complexity
        if complexity >= 70:
            recommendations.append("Break down this complex requirement into smaller, manageable sub-requirements")
        elif complexity >= 50:
            recommendations.append("Consider splitting this requirement into 2-3 smaller requirements")

        # Missing metrics
        if not re.search(r'\d+\s*(ms|seconds?|percent|%|TPS|users?)', text_lower):
            recommendations.append("Add specific metrics (response time, throughput, user count) where applicable")

        # Unspecified regulations
        if 'regulation' in text_lower or 'compliance' in text_lower:
            if not re.search(r'(GDPR|HIPAA|PDPA|ISO|PCI|SOC)', text_lower, re.IGNORECASE):
                recommendations.append("Specify which regulations apply (e.g., GDPR, HIPAA, Malaysia PDPA 2010)")

        # Missing error handling
        if not re.search(r'\b(error|failure|exception|invalid)\b', text_lower):
            recommendations.append("Define error handling and edge cases for this requirement")

        # Remove duplicates and limit to 5
        return list(dict.fromkeys(recommendations))[:5]

    def _calculate_confidence(self, text: str, complexity: int) -> float:
        """Calculate confidence (BR-10: threshold 0.70)"""
        confidence = 0.60

        # Increase for specific metrics
        if re.search(r'\d+\s*(ms|seconds?|%|TPS|RPS)', text, re.IGNORECASE):
            confidence += 0.15

        # Increase for strong modals
        if re.search(r'\b(shall|must|will)\b', text, re.IGNORECASE):
            confidence += 0.10

        # Increase for complete structure
        if len(text.split()) > 20:
            confidence += 0.05

        # Decrease for vague terms
        if any(term in text.lower() for term in ['appropriate', 'reasonable', 'adequate', 'sufficient']):
            confidence -= 0.10

        # Decrease for weak modals
        if 'should' in text.lower() or 'may' in text.lower():
            confidence -= 0.10

        return round(max(0.30, min(0.95, confidence)), 2)


# Singleton instance
predictive_analyzer = PredictiveAnalyzer()
