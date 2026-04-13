import re
from typing import Dict, List, Any
import math
from datetime import datetime

class PredictiveAnalyzer:
    def __init__(self):
        """
        Initialize the predictive analyzer
        """
        # Complexity factors and their weights
        self.complexity_factors = {
            "conditional_statements": {"weight": 1.2, "pattern": r'\b(if|when|unless|provided that|in case|assuming)\b'},
            "loop_statements": {"weight": 1.1, "pattern": r'\b(for|while|until|repeat|each|every)\b'},
            "nested_structures": {"weight": 1.5, "pattern": r'\b(and|or|but|however|although|despite|except when)\b'},
            "external_dependencies": {"weight": 1.3, "pattern": r'\b(integrate|connect to|interface with|communicate with|call|invoke|trigger)\b'},
            "error_handling": {"weight": 1.0, "pattern": r'\b(handle|catch|recover from|deal with|manage|resolve|solve)\b'},
            "security_considerations": {"weight": 1.4, "pattern": r'\b(secure|protect|encrypt|authenticate|authorize|permission|access control)\b'},
            "performance_requirements": {"weight": 1.3, "pattern": r'\b(fast|quick|efficient|responsive|optimized|scalable|concurrent|parallel)\b'},
            "data_processing": {"weight": 1.2, "pattern": r'\b(analyze|process|transform|convert|calculate|compute|aggregate)\b'},
            "state_management": {"weight": 1.1, "pattern": r'\b(store|maintain|track|remember|persist|cache|save|restore)\b'},
            "user_interaction": {"weight": 0.9, "pattern": r'\b(display|show|present|input|enter|click|select|choose)\b'}
        }

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for complexity and predict effort
        """
        if not text.strip():
            return {
                "complexity_score": 0.0,
                "estimated_effort_hours": 0.0,
                "risk_level": "low",
                "recommendations": [],
                "confidence_score": 0.0
            }

        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(text)
        
        # Estimate effort
        estimated_effort = self._estimate_effort(text, complexity_score)
        
        # Determine risk level
        risk_level = self._determine_risk_level(complexity_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(text, complexity_score)
        
        # Calculate confidence
        confidence_score = self._calculate_confidence(text, complexity_score)
        
        return {
            "complexity_score": complexity_score,
            "estimated_effort_hours": estimated_effort,
            "risk_level": risk_level,
            "recommendations": recommendations,
            "confidence_score": confidence_score
        }

    def _calculate_complexity_score(self, text: str) -> float:
        """
        Calculate complexity score based on various factors
        """
        text_lower = text.lower()
        total_score = 0.0
        
        for factor_name, factor_info in self.complexity_factors.items():
            pattern = factor_info["pattern"]
            weight = factor_info["weight"]
            
            matches = re.findall(pattern, text_lower)
            factor_score = len(matches) * weight
            total_score += factor_score
        
        # Normalize score to 0-100 range
        normalized_score = min(max(total_score * 3, 0.0), 100.0)  # Scale up for visibility
        return round(normalized_score, 1)

    def _estimate_effort(self, text: str, complexity_score: float) -> float:
        """
        Estimate development effort in hours based on complexity (0-100 scale).
        """
        # Base effort: roughly 1 hour per 10 words
        base_effort = len(text.split()) / 10

        # Complexity multiplier: 1.0 at score=0, up to 3.0 at score=100
        complexity_multiplier = 1.0 + (complexity_score / 100) * 2.0

        effort = base_effort * complexity_multiplier
        effort = max(effort, 1.0)  # Minimum 1 hour

        return round(effort, 2)

    def _determine_risk_level(self, complexity_score: float) -> str:
        """
        Determine risk level based on complexity score
        """
        if complexity_score <= 20:
            return "low"
        elif complexity_score <= 50:
            return "medium"
        elif complexity_score <= 80:
            return "high"
        else:
            return "critical"

    def _generate_recommendations(self, text: str, complexity_score: float) -> List[str]:
        """
        Generate recommendations based on analysis
        """
        recommendations = []
        
        text_lower = text.lower()
        
        # Add recommendations based on detected patterns
        if re.search(self.complexity_factors["conditional_statements"]["pattern"], text_lower):
            recommendations.append("Consider creating a decision table to clarify all conditional paths.")
        
        if re.search(self.complexity_factors["nested_structures"]["pattern"], text_lower):
            recommendations.append("Break down complex nested conditions into smaller, manageable functions.")
        
        if re.search(self.complexity_factors["external_dependencies"]["pattern"], text_lower):
            recommendations.append("Define clear contracts for external system interactions.")
        
        if re.search(self.complexity_factors["security_considerations"]["pattern"], text_lower):
            recommendations.append("Ensure security requirements are detailed and testable.")
        
        if re.search(self.complexity_factors["performance_requirements"]["pattern"], text_lower):
            recommendations.append("Specify concrete performance metrics (response time, throughput, etc.).")
        
        # Add general recommendations based on complexity level
        if complexity_score > 70:
            recommendations.extend([
                "Consider prototyping high-risk components first.",
                "Plan for extensive testing of complex interactions."
            ])
        elif complexity_score > 40:
            recommendations.append("Review requirements with stakeholders to ensure clarity.")
        
        # Add recommendation about documentation if not mentioned
        if "document" not in text_lower and "specification" not in text_lower:
            recommendations.append("Ensure all requirements are properly documented with acceptance criteria.")
        
        return recommendations[:5]  # Limit to top 5 recommendations

    def _calculate_confidence(self, text: str, complexity_score: float) -> float:
        """
        Calculate confidence in the analysis
        """
        # Base confidence on text length and analysis completeness
        text_length = len(text)
        base_confidence = min(text_length / 200, 0.6)  # Up to 0.6 for text length
        
        # Adjust based on complexity detection
        if complexity_score > 0:
            base_confidence += 0.2  # Bonus for detecting complexity
        
        # Adjust based on number of recommendations
        recommendations_count = len(self._generate_recommendations(text, complexity_score))
        recommendation_bonus = min(recommendations_count * 0.04, 0.2)  # Up to 0.2 bonus
        
        confidence = base_confidence + recommendation_bonus
        return round(max(0.1, min(1.0, confidence)), 2)  # Ensure between 0.1 and 1.0

    def analyze_requirements_quality(self, text: str) -> Dict[str, Any]:
        """
        Analyze the quality of requirements text
        """
        quality_indicators = {
            "clarity": self._assess_clarity(text),
            "completeness": self._assess_completeness(text),
            "consistency": self._assess_consistency(text),
            "testability": self._assess_testability(text)
        }
        
        # Calculate overall quality score
        avg_quality = sum(quality_indicators.values()) / len(quality_indicators)
        
        return {
            "quality_scores": quality_indicators,
            "overall_quality": avg_quality,
            "improvement_suggestions": self._generate_quality_improvements(text)
        }

    def _assess_clarity(self, text: str) -> float:
        """
        Assess clarity of the requirements text
        """
        clarity_score = 1.0
        
        # Penalize ambiguous terms
        ambiguous_terms = [
            r'\b(vague|unclear|not specified|not defined|maybe|perhaps|sometimes)\b',
            r'\b(etc\.|and so on|and others)\b',
            r'\b(soon|later|eventually|when possible)\b',
            r'\b(large|small|fast|slow|many|few)\b'
        ]
        
        for term_pattern in ambiguous_terms:
            matches = re.findall(term_pattern, text.lower())
            clarity_score -= len(matches) * 0.1
        
        return max(0.0, min(1.0, clarity_score))

    def _assess_completeness(self, text: str) -> float:
        """
        Assess completeness of the requirements
        """
        # Look for common missing elements
        completeness_score = 0.5  # Base score
        
        # Check for presence of key elements
        if re.search(r'\b(actor|user|role|person|system)\b', text, re.IGNORECASE):
            completeness_score += 0.1
        
        if re.search(r'\b(input|output|data|information)\b', text, re.IGNORECASE):
            completeness_score += 0.1
        
        if re.search(r'\b(condition|constraint|limitation|restriction)\b', text, re.IGNORECASE):
            completeness_score += 0.1
        
        if re.search(r'\b(error|exception|failure|problem)\b', text, re.IGNORECASE):
            completeness_score += 0.1
        
        if re.search(r'\b(test|verify|confirm|ensure)\b', text, re.IGNORECASE):
            completeness_score += 0.1
        
        return min(1.0, completeness_score)

    def _assess_consistency(self, text: str) -> float:
        """
        Assess consistency of the requirements
        """
        # Look for contradictory terms
        contradiction_indicators = [
            r'\b(but|however|nevertheless|on the other hand|yet|although|though)\b',
            r'\b(contradicts|conflicts with|opposes|inconsistent with)\b'
        ]
        
        consistency_score = 1.0
        
        for indicator_pattern in contradiction_indicators:
            matches = re.findall(indicator_pattern, text.lower())
            consistency_score -= len(matches) * 0.2
        
        return max(0.0, min(1.0, consistency_score))

    def _assess_testability(self, text: str) -> float:
        """
        Assess testability of the requirements
        """
        testability_score = 0.3  # Base score
        
        # Look for measurable terms
        measurable_patterns = [
            r'\b(measure|count|quantify|verify|validate|test|check)\b',
            r'\b(seconds|minutes|hours|days|percent|ratio|size|amount|frequency)\b',
            r'\b(less than|greater than|equal to|within|between|above|below)\b'
        ]
        
        for pattern in measurable_patterns:
            matches = re.findall(pattern, text.lower())
            testability_score += len(matches) * 0.1
        
        return min(1.0, testability_score)

    def _generate_quality_improvements(self, text: str) -> List[str]:
        """
        Generate specific improvement suggestions
        """
        improvements = []
        
        if self._assess_clarity(text) < 0.7:
            improvements.append("Use more specific terminology and avoid ambiguous terms.")
        
        if self._assess_completeness(text) < 0.7:
            improvements.append("Include more details about actors, inputs, outputs, and constraints.")
        
        if self._assess_testability(text) < 0.7:
            improvements.append("Add measurable criteria and quantitative requirements.")
        
        if self._assess_consistency(text) < 0.7:
            improvements.append("Review for conflicting statements and resolve contradictions.")
        
        return improvements