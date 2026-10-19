"""
Model Evaluation Harness - VisSpec FYP (Section 4.8.1)

Evaluates THREE genuinely distinct paths on a held-out test set:

  1. RULES     : Validator(use_llm=False)                    - local rules only
  2. LLM-only  : LLMValidator().validate_requirement() direct - NO rule fallback
  3. HYBRID    : Validator(use_llm=True)                     - LLM-first, rule fallback

Integrity rules (reviewer protocol):
  * A failed or malformed LLM call is recorded as llm_failed and is NEVER
    counted as an LLM verdict. If ANY required LLM call fails, the whole run
    is marked INCOMPLETE and the script exits non-zero.
  * Two threshold settings are reported separately for every path:
      no_threshold  - any reported defect counts (raw confidences preserved)
      br10_enforced - only defects with confidence >= 0.70 count (BR-10)
  * Provenance is saved: git commit, timestamp, model id, temperature,
    max_tokens, split seed, dataset name/size, prompt SHA-256.
  * A pre-existing evaluation_results.json is renamed (preserved for audit)
    before any new results are written.

Run ONLY after backend/_smoke_test.py PASSES (protocol step 4):
    python3 backend/evaluate_model.py --dataset held_out_test_set

Exit codes: 0 = COMPLETE, 2 = INCOMPLETE (required LLM call failed),
            1 = harness error.

Author: Mohammed Aamena Mohammed Abdulkarem (1221305728)
"""

import json
import subprocess
import sys
import time
import argparse
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.core.config import settings
from backend.services.validation.validator import Validator
from backend.services.ai.llm_validator import LLMValidator, PROMPT_SHA256

# BR-10: minimum confidence for a defect to count (IEEE 830 / report Section 2.3.3).
CONFIDENCE_THRESHOLD = 0.70
# Must match the payload llm_validator actually sends; recorded for provenance.
MAX_TOKENS = 2048
# Seed used by backend/test_data/split_dataset.py to freeze dev/held-out split.
SPLIT_SEED = 42
# Baseline targets were established internally during the FYP1 prototyping phase
# based on initial rule-based performance. They are NOT an external benchmark.
BASELINE_TARGETS = {
    "precision": 0.843,
    "recall": 0.781,
    "f1": 0.810,
    "origin": "Established internally during the FYP1 prototyping phase based on "
              "initial rule-based performance (not an external benchmark).",
}


def load_dataset(name: str = "held_out_test_set") -> List[Dict]:
    """Load an evaluation dataset by name (without .json) from backend/test_data/."""
    dataset_path = Path(__file__).parent / "test_data" / f"{name}.json"
    if not dataset_path.exists():
        print(f"❌ Dataset not found at {dataset_path}")
        sys.exit(1)
    with open(dataset_path, "r") as f:
        return json.load(f)


def git_commit() -> str:
    """Current HEAD commit hash, or 'unknown' if git is unavailable."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _compact_defects(defects: List[Dict]) -> List[Dict]:
    """Per-defect record: type, RAW confidence (never rounded), evidence."""
    return [
        {
            "type": d.get("type"),
            "confidence": d.get("confidence"),
            "evidence": d.get("evidence"),
            "description": (d.get("description") or "")[:120],
        }
        for d in defects
    ]


def _type_counts(defects: List[Dict]) -> Dict[str, int]:
    """Count defects per type (raw, pre-threshold)."""
    counts: Dict[str, int] = {}
    for d in defects:
        t = d.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


def _metrics(tp: int, fp: int, fn: int, tn: int, total_time: float, n: int) -> Dict:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + fp + fn + tn) if n else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "accuracy": accuracy,
        "specificity": specificity,
        "avg_response_time_ms": round((total_time / n) * 1000, 1) if n else 0.0,
    }


def run_case_rules(text: str, validator: Validator) -> Dict[str, Any]:
    """RULES path: local validator only. Never an LLM verdict."""
    t0 = time.time()
    result = validator.validate_text(text)
    elapsed = time.time() - t0
    defects = result.get("raw_defects", result.get("defects", []))
    return {
        "defects": defects,            # raw, unfiltered
        "llm_used": False,
        "llm_failed": False,           # LLM not required for this path
        "model_used": None,
        "json_parse_ok": None,
        "error": None,
        "elapsed_ms": round(elapsed * 1000, 1),
    }


def run_case_llm_only(text: str, llm_validator: LLMValidator) -> Dict[str, Any]:
    """LLM-ONLY path: LLMValidator directly. NO rule fallback whatsoever."""
    t0 = time.time()
    result = llm_validator.validate_requirement(text)
    elapsed = time.time() - t0
    llm_used = bool(result.get("llm_used"))
    json_ok = result.get("json_parse_ok", False)
    return {
        "defects": result.get("defects", []),   # raw defects (pre-BR-10)
        "llm_used": llm_used,
        # Failed request OR malformed JSON -> llm_failed; never an LLM verdict.
        "llm_failed": not (llm_used and json_ok),
        "model_used": result.get("model_used"),
        "json_parse_ok": json_ok,
        "error": result.get("error"),
        "elapsed_ms": round(elapsed * 1000, 1),
    }


def run_case_hybrid(text: str, validator: Validator) -> Dict[str, Any]:
    """HYBRID path: Validator(use_llm=True) = LLM-first, rule fallback.

    llm_failed is True when the LLM was attempted but did not genuinely answer
    (call failed or JSON malformed) — rules then silently supplied the verdict,
    which must not be presented as an LLM result.
    """
    t0 = time.time()
    result = validator.validate_text(text)
    elapsed = time.time() - t0
    llm_used = bool(result.get("llm_used"))
    json_ok = result.get("llm_json_parse_ok")
    llm_attempted = ("llm_model_used" in result) or llm_used
    return {
        "defects": result.get("raw_defects", result.get("defects", [])),
        "llm_used": llm_used,
        "llm_failed": bool(llm_attempted and not llm_used),
        "model_used": result.get("llm_model_used"),
        "json_parse_ok": json_ok,
        "error": result.get("llm_error"),
        "elapsed_ms": round(elapsed * 1000, 1),
    }


def run_path(path_name: str, test_data: List[Dict], case_runner, verbose: bool,
             inter_case_delay_s: float = 0.0) -> Dict:
    """Evaluate one path over the dataset.

    Two threshold settings are computed per case from the SAME raw defect list:
      no_threshold : any raw defect counts
      br10_enforced: only defects with confidence >= CONFIDENCE_THRESHOLD

    inter_case_delay_s: optional pause between cases — the anonymous LLM
    tier rate-limits bursts, so LLM paths pass a small delay to avoid 429s.
    """
    counters = {
        "no_threshold": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
        "br10_enforced": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
    }
    llm_answered = 0
    llm_failed_cases = 0
    total_ms = 0.0
    results: List[Dict] = []

    print(f"\n🔍 [{path_name}] Running {len(test_data)} predictions...")
    print("-" * 80)

    for i, item in enumerate(test_data, 1):
        if inter_case_delay_s and i > 1:
            time.sleep(inter_case_delay_s)  # pace requests; avoid provider 429s
        text = item["text"]
        expert = item["expert_verdict"]
        expert_defect = (expert == "DEFECT")

        out = case_runner(text)
        total_ms += out["elapsed_ms"]
        if out["llm_used"]:
            llm_answered += 1
        if out["llm_failed"]:
            llm_failed_cases += 1

        raw = out["defects"]
        qualifying_br10 = [d for d in raw
                           if float(d.get("confidence", 0.0)) >= CONFIDENCE_THRESHOLD]

        preds = {
            "no_threshold": len(raw) > 0,
            "br10_enforced": len(qualifying_br10) > 0,
        }
        conf = max([float(d.get("confidence", 0.0)) for d in raw], default=0.0)

        verdicts = {}
        for setting, pred in preds.items():
            c = counters[setting]
            if pred and expert_defect:
                c["tp"] += 1; verdicts[setting] = "TP"
            elif pred and not expert_defect:
                c["fp"] += 1; verdicts[setting] = "FP"
            elif not pred and expert_defect:
                c["fn"] += 1; verdicts[setting] = "FN"
            else:
                c["tn"] += 1; verdicts[setting] = "TN"

        if verbose:
            v = verdicts["br10_enforced"]
            symbol = "✓" if v in ("TP", "TN") else "✗"
            extra = " [LLM-FAILED]" if out["llm_failed"] else ""
            print(f"[{i:02d}] {symbol} {v:2} | Expert: {expert:8} | "
                  f"raw defects: {len(raw):2} | conf: {conf:.2f} | "
                  f"{text[:40]}...{extra}")

        results.append({
            "id": item["id"],
            "text": text[:70] + ("..." if len(text) > 70 else ""),
            "expert": expert,
            "expert_defect_type": item.get("defect_type"),
            # vis_prediction + confidence are the UNTHRESHOLDed view so that
            # scripts/01_eval_report.py can reconstruct any threshold row
            # (pred = vis_prediction AND confidence >= th).
            "vis_prediction": "DEFECT" if preds["no_threshold"] else "NO_DEFECT",
            "vis_prediction_br10": "DEFECT" if preds["br10_enforced"] else "NO_DEFECT",
            "confidence": round(conf, 3),
            "defect_type_counts": _type_counts(raw),
            "verdict_br10": verdicts["br10_enforced"],
            "verdict_no_threshold": verdicts["no_threshold"],
            "defects_raw": _compact_defects(raw),
            "llm_used": out["llm_used"],
            "llm_failed": out["llm_failed"],
            "model_used": out["model_used"],
            "json_parse_ok": out["json_parse_ok"],
            "error": out["error"],
            "elapsed_ms": out["elapsed_ms"],
        })

    n = len(test_data)
    print(f"\nLLM answered {llm_answered} of {n} cases "
          f"({llm_failed_cases} llm_failed)  [{path_name}]")

    settings_out = {}
    for setting, c in counters.items():
        settings_out[setting] = {
            "confusion_matrix": dict(c),
            "metrics": _metrics(c["tp"], c["fp"], c["fn"], c["tn"], total_ms, n),
        }

    return {
        "path": path_name,
        "dataset_size": n,
        "llm_answered_cases": llm_answered,
        "llm_failed_cases": llm_failed_cases,
        "status": "INCOMPLETE" if llm_failed_cases > 0 else "COMPLETE",
        "settings": settings_out,
        "detailed_results": results,
    }


def evaluate_model(dataset_name: str = "held_out_test_set", verbose: bool = True) -> int:
    """Main evaluation. Returns process exit code (0=COMPLETE, 2=INCOMPLETE)."""
    print("\n" + "=" * 80)
    print("VISSPEC MODEL EVALUATION — RULES vs LLM-ONLY vs HYBRID")
    print("BR-10 confidence threshold = " f"{CONFIDENCE_THRESHOLD} (applied in code)")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    test_data = load_dataset(dataset_name)
    print(f"\n📊 Loaded {len(test_data)} cases from {dataset_name}.json")

    llm_validator = LLMValidator()
    if not llm_validator.is_available:
        print(f"❌ LLM profile '{settings.LLM_PROFILE}' unavailable — LLM paths cannot run. ABORTING.")
        return 2

    rules_validator = Validator(use_llm=False)
    hybrid_validator = Validator(use_llm=True)

    # The anonymous endpoint rate-limits bursts (HTTP 429) with a rolling
    # window; 15s between LLM cases keeps the run under the anonymous-tier cap.
    LLM_CASE_DELAY_S = 15.0

    paths: Dict[str, Dict] = {}
    paths["rules"] = run_path(
        "RULES", test_data, lambda t: run_case_rules(t, rules_validator), verbose)
    paths["llm"] = run_path(
        "LLM-only", test_data, lambda t: run_case_llm_only(t, llm_validator),
        verbose, inter_case_delay_s=LLM_CASE_DELAY_S)
    paths["hybrid"] = run_path(
        "HYBRID", test_data, lambda t: run_case_hybrid(t, hybrid_validator),
        verbose, inter_case_delay_s=LLM_CASE_DELAY_S)

    # --- Comparison table (BR-10 enforced setting) ---
    print("\n" + "=" * 80)
    print("PATH COMPARISON — br10_enforced (confidence >= 0.70)")
    print("=" * 80)
    print(f"{'Path':<10} {'TP':>3} {'FP':>3} {'FN':>3} {'TN':>3} | "
          f"{'Prec':>7} {'Recall':>7} {'F1':>7} | {'LLM-ans':>7} {'Failed':>6} {'Status':>10}")
    print("-" * 80)
    any_incomplete = False
    for key in ["rules", "llm", "hybrid"]:
        p = paths[key]
        m = p["settings"]["br10_enforced"]["metrics"]
        cm = p["settings"]["br10_enforced"]["confusion_matrix"]
        if p["status"] != "COMPLETE":
            any_incomplete = True
        print(f"{p['path']:<10} {cm['tp']:>3} {cm['fp']:>3} {cm['fn']:>3} {cm['tn']:>3} | "
              f"{m['precision']:>6.1%} {m['recall']:>7.1%} {m['f1_score']:>7.1%} | "
              f"{p['llm_answered_cases']:>7} {p['llm_failed_cases']:>6} {p['status']:>10}")

    # --- Save with full provenance ---
    results_file = Path(__file__).parent / "evaluation_results.json"
    if results_file.exists():
        audit_copy = results_file.with_name("evaluation_results_OLD_buggy.json")
        results_file.replace(audit_copy)
        print(f"\n📦 Previous results preserved as {audit_copy.name}")

    run_status = "INCOMPLETE" if any_incomplete else "COMPLETE"
    provenance = {
        "git_commit": git_commit(),
        "timestamp": datetime.now().isoformat(),
        "model_id": settings.llm_model_id,
        "profile": settings.LLM_PROFILE,
        "endpoint_host": settings.llm_host,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "response_format": "json_object",
        "prompt_sha256": PROMPT_SHA256,
        "prompt_file": "backend/services/ai/prompts_v2.txt",
        "split_seed": SPLIT_SEED,
        "split_note": "dev_set.json / held_out_test_set.json frozen via "
                      "backend/test_data/split_dataset.py (seed 42); rules and "
                      "prompts tuned on dev only.",
        "dataset": f"{dataset_name}.json",
        "dataset_size": len(test_data),
        "confidence_threshold": CONFIDENCE_THRESHOLD,
    }

    with open(results_file, "w") as f:
        json.dump({
            "status": run_status,
            "status_note": ("Some required LLM call(s) failed — LLM/Hybrid metrics "
                            "are NOT valid LLM results. Re-run after fixing "
                            "connectivity/model access." if any_incomplete else
                            "All required LLM calls succeeded."),
            "provenance": provenance,
            "baseline": BASELINE_TARGETS,
            "paths": {
                k: {kk: vv for kk, vv in v.items() if kk != "detailed_results"}
                for k, v in paths.items()
            },
            # Top-level detailed_results kept for scripts/01_eval_report.py:
            # hybrid path, BR-10 enforced view (matches paper's reported path).
            "detailed_results": paths["hybrid"]["detailed_results"],
            "detailed_results_by_path": {
                k: v["detailed_results"] for k, v in paths.items()
            },
        }, f, indent=2)

    print(f"\n📁 Results saved to: {results_file}")
    if any_incomplete:
        print("\n⚠️  STATUS: INCOMPLETE — at least one required LLM call failed.")
        print("   LLM-only and Hybrid metrics above MUST NOT be reported as")
        print("   LLM-generated results until every call succeeds.")
        print("=" * 80 + "\n")
        return 2
    print("\n✅ STATUS: COMPLETE — every required LLM call succeeded.")
    print("=" * 80 + "\n")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VisSpec model evaluation")
    parser.add_argument("--dataset", default="held_out_test_set",
                        help="Dataset name in backend/test_data (default: held_out_test_set)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-case output; show summaries only")
    args = parser.parse_args()
    try:
        sys.exit(evaluate_model(dataset_name=args.dataset, verbose=not args.quiet))
    except SystemExit:
        raise
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
