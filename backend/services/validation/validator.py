"""
Main validation orchestrator.
Coordinates ambiguity detection, consistency checking, and completeness analysis.
"""
import time
from typing import List, Dict, Any, Optional
import difflib

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.services.validation.ambiguity_detector import AmbiguityDetector
from backend.services.validation.consistency_checker import ConsistencyChecker
from backend.services.validation.completeness_analyzer import CompletenessAnalyzer
from backend.services.ai.llm_service import llm_service
from backend.services.ai.llm_validator import LLMValidator
from backend.services.ai.requirement_organizer import RequirementOrganizer

logger = get_logger(__name__)


class Validator:
    """Orchestrates the full validation pipeline for requirements."""

    # Modal verbs ranked by strength (weaker = more likely to cause ambiguity)
    MODAL_STRENGTH = {
        "shall": 5,
        "must": 5,
        "will": 4,
        "should": 3,
        "may": 2,
        "might": 1,
        "could": 1,
        "would": 2,
        "can": 3,
    }

    # Categories that should use strong modal verbs
    STRONG_MODAL_CATEGORIES = {"functional", "constraint", "security"}

    def __init__(self, use_llm: bool = True, mode: str = "llm_first"):
        """
        Args:
            use_llm: enable the LLM-first path (False = rules only).
            mode: hybrid combination strategy —
                  "llm_first" = rules run ONLY when the LLM returns no
                               usable defects (default; described in paper);
                  "union"    = rule defects are always merged with LLM
                               defects (deduplicated by type+confidence).
                  Selected on the DEV set only (see experiments_dev.md /
                  FREEZE.md); never re-chosen after the pre-test freeze.
        """
        if mode not in ("llm_first", "union"):
            raise ValueError(f"Unknown hybrid mode: {mode!r} "
                             "(expected 'llm_first' or 'union')")
        self.ambiguity_detector = AmbiguityDetector()
        self.consistency_checker = ConsistencyChecker()
        self.completeness_analyzer = CompletenessAnalyzer()
        self.use_llm = use_llm
        self.mode = mode
        self.llm_validator = LLMValidator() if use_llm else None
        self.llm_service = llm_service if use_llm else None

    def validate_text(self, text: str) -> Dict[str, Any]:
        """
        Run full validation pipeline on a block of requirements text.
        Tries LLM first, falls back to rule-based if unavailable.
        Returns structured validation results.
        """
        start_time = time.time()
        all_defects = []
        llm_result = None

        # 1. Try enhanced LLM validation first (if available)
        llm_meta: Dict[str, Any] = {}
        if self.use_llm and self.llm_validator and self.llm_validator.is_available:
            try:
                llm_result = self.llm_validator.validate_requirement(text)
                # Production pipeline uses the BR-10-filtered list (threshold is
                # applied in llm_validator code, not the prompt). The raw list is
                # kept on the result for evaluations that sweep the threshold.
                llm_defects = llm_result.get("filtered_defects") or llm_result.get("defects", [])
                all_defects.extend(llm_defects)
                logger.info(f"Enhanced LLM validation found {len(llm_defects)} defects (BR-10 applied)")
                # Trust the LLM validator's own llm_used flag. It is True only when the
                # provider actually answered; it is False when the call failed or the
                # model returned no usable response. Forcing it True here would mislabel
                # a rule-based fallback as an LLM verdict (the exact issue flagged in
                # review: headline numbers must reflect the path that produced them).
                llm_result["llm_used"] = bool(llm_result.get("llm_used", False))
                # Per-case provenance for the evaluation harness (step 2 of protocol):
                llm_meta = {
                    "llm_model_used": llm_result.get("model_used"),
                    "llm_json_parse_ok": llm_result.get("json_parse_ok", False),
                    "llm_error": llm_result.get("error"),
                    "llm_raw_defects": llm_result.get("defects", []),
                }
                # Note: Zero-retention is a policy guarantee of the Groq API provider,
                # not a locally enforced code feature. Local PII redaction is applied in
                # privacy.py / text_cleaner.py before any text is sent to the provider.
            except Exception as e:
                logger.warning(f"Enhanced LLM validation failed: {e}. Falling back to rule-based.")
                llm_result = {"llm_used": False, "error": str(e)}
                llm_meta = {"llm_model_used": None, "llm_json_parse_ok": False,
                            "llm_error": str(e), "llm_raw_defects": []}

        # 2. Rule-based validation. llm_first mode: runs only when the LLM
        # produced nothing usable (the documented hybrid strategy). union
        # mode: always runs and merges with the LLM verdicts.
        rule_defects: List[Dict[str, Any]] = []
        run_rules = (
            not self.use_llm
            or not all_defects
            or self.mode == "union"
        )
        if run_rules:
            logger.info("Running rule-based validation")
            # Ambiguity detection (rule-based)
            rule_defects.extend(self.ambiguity_detector.analyze(text))
            # Completeness analysis
            rule_defects.extend(self.completeness_analyzer.analyze(text))
            # Consistency checking
            rule_defects.extend(self.consistency_checker.check_single(text))
            all_defects.extend(rule_defects)

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Unfiltered view for threshold-sweep evaluations: raw LLM defects exactly
        # as returned (pre BR-10) plus any rule defects that ran. This never feeds
        # the application pipeline — it exists so the evaluation can report both
        # no_threshold and br10_enforced settings from one run.
        raw_defects = list(llm_meta.get("llm_raw_defects", [])) + rule_defects

        return self._build_result(all_defects, processing_time_ms, llm_result, llm_meta, raw_defects)

    def validate_requirements_with_context(
        self,
        requirements: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate enriched requirements using classification context.
        
        Args:
            requirements: List of requirement dicts with keys:
                req_id, original_text, category, vague_terms, modal_verbs
        
        Returns:
            Validation result with defects mapped to specific requirements.
        """
        start_time = time.time()
        all_defects = []
        req_texts = []

        for req in requirements:
            text = req.get("original_text", "")
            req_texts.append(text)
            req_id = req.get("req_id")

            # Run base validation on individual requirement
            base_defects = self._validate_single_requirement(text)
            
            # Enhance defects with classification context
            enhanced = self._enhance_with_context(base_defects, req)
            for d in enhanced:
                d["req_id"] = req_id
            all_defects.extend(enhanced)

            # Add classification-based defects (vague terms, weak modals)
            classification_defects = self._detect_classification_issues(req)
            for d in classification_defects:
                d["req_id"] = req_id
            all_defects.extend(classification_defects)

        # Cross-requirement consistency check
        cross_defects = self.consistency_checker.check_multiple(req_texts)
        for cd in cross_defects:
            # Map cross defects to the most similar requirement
            best_req_id = self._find_best_match(cd.get("text", ""), requirements)
            cd["req_id"] = best_req_id
            all_defects.append(cd)

        processing_time_ms = int((time.time() - start_time) * 1000)
        return self._build_result(all_defects, processing_time_ms, None)

    def _validate_single_requirement(self, text: str) -> List[Dict[str, Any]]:
        """Run base validation on a single requirement text."""
        defects = []
        defects.extend(self.ambiguity_detector.analyze(text))
        defects.extend(self.completeness_analyzer.analyze(text))
        defects.extend(self.consistency_checker.check_single(text))
        return defects

    def _enhance_with_context(
        self,
        defects: List[Dict[str, Any]],
        req: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Enhance defect severity based on classification data.
        """
        vague_terms = req.get("vague_terms", []) or []
        modal_verbs = req.get("modal_verbs", []) or []
        category = req.get("category", "functional")

        # Boost severity for defects when vague terms are present
        if vague_terms:
            for d in defects:
                if d.get("type") == "ambiguity" and d.get("severity") != "high":
                    d["severity"] = "high"
                    d["description"] = f"{d['description']} [Enhanced: vague terms detected: {', '.join(vague_terms)}]"

        # Boost severity for constraint/functional requirements with weak modal verbs
        if category in self.STRONG_MODAL_CATEGORIES and modal_verbs:
            weakest_strength = min(
                self.MODAL_STRENGTH.get(mv.lower(), 5) for mv in modal_verbs
            )
            if weakest_strength < 3:
                for d in defects:
                    if d.get("type") in ("ambiguity", "unverifiable"):
                        d["severity"] = "high"
                        d["description"] = f"{d['description']} [Enhanced: weak modal verb '{modal_verbs[0]}' in {category} requirement]"

        return defects

    def _detect_classification_issues(self, req: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect issues based purely on classification data.
        """
        defects = []
        vague_terms = list(req.get("vague_terms") or [])
        modal_verbs = req.get("modal_verbs", []) or []
        category = req.get("category", "functional")
        text = req.get("original_text", "")

        # Heuristic vague terms if enrichment/LLM entity pass left the list empty
        if not vague_terms and text:
            text_lower = text.lower()
            for vt in RequirementOrganizer.VAGUE_TERMS:
                if vt.lower() in text_lower and vt not in vague_terms:
                    vague_terms.append(vt)

        # Defect: vague terms present
        if vague_terms:
            defects.append({
                "text": text[:200],
                "type": "ambiguity",
                "severity": "medium",
                "confidence": 0.85,
                "description": f"Requirement contains vague terms that make it unverifiable: {', '.join(vague_terms)}",
                "suggestion": f"Replace vague terms with measurable criteria. For example, instead of '{vague_terms[0]}', specify exact thresholds or conditions.",
            })

        # Defect: weak modal verbs in critical categories
        if category in self.STRONG_MODAL_CATEGORIES and modal_verbs:
            weakest = min(modal_verbs, key=lambda mv: self.MODAL_STRENGTH.get(mv.lower(), 5))
            strength = self.MODAL_STRENGTH.get(weakest.lower(), 5)
            if strength < 3:
                defects.append({
                    "text": text[:200],
                    "type": "unverifiable",
                    "severity": "medium",
                    "confidence": 0.75,
                    "description": f"{category.capitalize()} requirement uses weak modal verb '{weakest}'. This creates ambiguity about whether the requirement is mandatory.",
                    "suggestion": f"Use 'shall' or 'must' instead of '{weakest}' to make this requirement mandatory and testable.",
                })

        # Defect: missing modal verb entirely
        if not modal_verbs and len(text.split()) > 3:
            defects.append({
                "text": text[:200],
                "type": "incompleteness",
                "severity": "low",
                "confidence": 0.6,
                "description": "No modal verb (shall, must, should, will, may) detected. Requirements should use standard modal verbs for clarity.",
                "suggestion": "Add a modal verb like 'shall' or 'must' to clarify whether this is mandatory or optional.",
            })

        return defects

    def _find_best_match(self, defect_text: str, requirements: List[Dict[str, Any]]) -> Optional[str]:
        """
        Find the requirement that best matches the defect text using
        difflib.SequenceMatcher for text similarity.
        """
        if not defect_text or not requirements:
            return requirements[0].get("req_id") if requirements else None

        best_ratio = 0.0
        best_req_id = None

        for req in requirements:
            req_text = req.get("original_text", "")
            if not req_text:
                continue
            ratio = difflib.SequenceMatcher(None, defect_text.lower(), req_text.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_req_id = req.get("req_id")

        return best_req_id

    def _build_result(
        self,
        all_defects: List[Dict[str, Any]],
        processing_time_ms: int,
        llm_result: Optional[Dict[str, Any]],
        llm_meta: Optional[Dict[str, Any]] = None,
        raw_defects: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build the final validation result dict."""
        total_defects = len(all_defects)
        high_severity = sum(1 for d in all_defects if d.get("severity") == "high")
        medium_severity = sum(1 for d in all_defects if d.get("severity") == "medium")
        low_severity = sum(1 for d in all_defects if d.get("severity") == "low")

        # More realistic scoring: start from baseline and deduct proportionally
        # Base score of 70% for typical SRS, deduct based on severity
        base_score = 0.70
        max_deduction = 0.60  # Maximum 60% deduction, score won't go below 10%
        
        # Calculate proportional deductions (more lenient)
        deductions = (high_severity * 0.05) + (medium_severity * 0.025) + (low_severity * 0.01)
        deductions = min(deductions, max_deduction)  # Cap the deduction
        
        score = round(max(0.10, min(1.0, base_score - deductions)), 2)

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
                "low": low_severity,
            },
            "defects": all_defects,
            # Report llm_used faithfully: True only when the LLM validator actually
            # produced the result (llm_result["llm_used"] is True). A failed call leaves
            # llm_result as a non-None dict with llm_used=False, so checking `is not None`
            # alone would wrongly claim the LLM answered when rules supplied the defects.
            "llm_used": bool(self.use_llm and llm_result and llm_result.get("llm_used", False)),
            # Per-case LLM provenance for the evaluation harness. Empty dict for
            # paths that never attempted an LLM call (rules-only / context path).
            **(llm_meta or {}),
            # Unfiltered defect view (pre BR-10) for threshold-sweep evaluations.
            "raw_defects": raw_defects if raw_defects is not None else all_defects,
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
