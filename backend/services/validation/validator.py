"""
Main validation orchestrator.
Coordinates ambiguity detection, consistency checking, and completeness analysis.
"""
import time
from typing import List, Dict, Any, Optional

from core.config import settings
from core.logging import get_logger
from services.validation.ambiguity_detector import AmbiguityDetector
from services.validation.consistency_checker import ConsistencyChecker
from services.validation.completeness_analyzer import CompletenessAnalyzer
from services.ai.llm_service import llm_service

logger = get_logger(__name__)


class Validator:
    """Orchestrates the full validation pipeline for requirements."""

    def __init__(self, use_llm: bool = True):
        self.ambiguity_detector = AmbiguityDetector()
        self.consistency_checker = ConsistencyChecker()
        self.completeness_analyzer = CompletenessAnalyzer()
        self.use_llm = use_llm and llm_service.is_available

    def validate_text(self, text: str) -> Dict[str, Any]:
        """
        Run full validation pipeline on a block of requirements text.
        Returns structured validation results.
        """
        start_time = time.time()
        all_defects = []

        # 1. Ambiguity detection (rule-based)
        ambiguity_defects = self.ambiguity_detector.analyze(text)
        all_defects.extend(ambiguity_defects)

        # 2. Completeness analysis
        completeness_defects = self.completeness_analyzer.analyze(text)
        all_defects.extend(completeness_defects)

        # 3. Consistency checking
        consistency_defects = self.consistency_checker.check_single(text)
        all_defects.extend(consistency_defects)

        # 4. LLM-enhanced analysis (if available)
        llm_result = None
        if self.use_llm:
            try:
                llm_result = llm_service.analyze_ambiguity(text)
                llm_defects = llm_result.get("defects", [])
                # Merge LLM defects, avoiding duplicates
                existing_texts = {d["text"] for d in all_defects}
                for defect in llm_defects:
                    if defect["text"] not in existing_texts:
                        all_defects.append(defect)
            except Exception as e:
                logger.warning(f"LLM analysis failed, using rule-based only: {e}")

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Calculate overall score on 0.0–1.0 scale
        total_defects = len(all_defects)
        high_severity = sum(1 for d in all_defects if d.get("severity") == "high")
        medium_severity = sum(1 for d in all_defects if d.get("severity") == "medium")
        low_severity = sum(1 for d in all_defects if d.get("severity") == "low")

        # Weighted deduction: high defects hurt most, then medium, then low
        deductions = (high_severity * 0.15) + (medium_severity * 0.08) + (low_severity * 0.03)
        score = round(max(0.0, min(1.0, 1.0 - deductions)), 2)

        return {
            "overall_score": score,
            "total_defects": total_defects,
            "defects_by_type": {
                "ambiguity": sum(1 for d in all_defects if d["type"] == "ambiguity"),
                "incompleteness": sum(1 for d in all_defects if d["type"] == "incompleteness"),
                "inconsistency": sum(1 for d in all_defects if d["type"] == "inconsistency"),
                "unverifiable": sum(1 for d in all_defects if d["type"] == "unverifiable"),
            },
            "defects_by_severity": {
                "high": high_severity,
                "medium": medium_severity,
                "low": sum(1 for d in all_defects if d.get("severity") == "low"),
            },
            "defects": all_defects,
            "llm_used": self.use_llm and llm_result is not None,
            "processing_time_ms": processing_time_ms,
        }

    def validate_multiple(self, requirements: List[str]) -> Dict[str, Any]:
        """Validate multiple requirement texts."""
        all_results = []
        total_defects = 0

        for req in requirements:
            result = self.validate_text(req)
            all_results.append(result)
            total_defects += result["total_defects"]

        # Cross-requirement consistency check
        cross_defects = self.consistency_checker.check_multiple(requirements)
        total_defects += len(cross_defects)

        avg_score = round(sum(r["overall_score"] for r in all_results) / len(all_results), 2) if all_results else 1.0

        return {
            "overall_score": avg_score,
            "total_defects": total_defects,
            "requirement_count": len(requirements),
            "cross_requirement_defects": cross_defects,
            "per_requirement": all_results,
        }
