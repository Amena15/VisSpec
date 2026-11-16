#!/usr/bin/env python3
"""
extract_rule_metrics.py  --  Extract Precision / Recall / F1 for the rule-based
(VisSpec "rules") path from an evaluation JSON file.

Usage (run from the repo root):
    python scripts/extract_rule_metrics.py \
        --file backend/evaluation_results_groq-gpt-oss-120b_run3.json

Defaults to backend/evaluation_results_groq-gpt-oss-120b_run3.json. If that file
(or the one passed via --file) contains no rule-based results, the script scans
sibling evaluation*.json files and uses the first one that does.

The rule results live under the "rules" key. In the current harness layout they
are at detailed_results_by_path.rules (a list of per-case dicts). The script
also accepts a top-level "rules" list.

Each rule case carries:
    expert            - ground-truth verdict ("DEFECT" / "NO_DEFECT")
    vis_prediction    - rule-based verdict ("DEFECT" / "NO_DEFECT")
    confidence        - reported confidence (0.0 for pure rules; may be set)

Metrics (same convention as backend/evaluate_model.py):
    TP  expert == DEFECT  and vis_prediction == DEFECT
    FP  expert == NO_DEFECT and vis_prediction == DEFECT
    FN  expert == DEFECT  and vis_prediction == NO_DEFECT

    Precision = TP / (TP + FP)      (0.0 if TP + FP == 0)
    Recall    = TP / (TP + FN)      (0.0 if TP + FN == 0)
    F1-score  = 2 * P * R / (P + R) (0.0 if P + R == 0)

With --threshold (default 0.0) a predicted defect only counts when
confidence >= threshold; use --threshold 0.70 to reproduce the BR-10 setting.

If the JSON instead stores raw counts (tp / fp / fn) anywhere in its tree,
those are used directly and no per-case recounting is done.
"""
import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = REPO_ROOT / "backend" / "evaluation_results_groq-gpt-oss-120b_run3.json"

POSITIVE = "DEFECT"
CONFIDENCE_FIELD = "confidence"


def find_rules_key(data):
    """Return the list of per-case rule results stored under a "rules" key."""
    if isinstance(data.get("rules"), list):
        return data["rules"]
    drbp = data.get("detailed_results_by_path")
    if isinstance(drbp, dict) and isinstance(drbp.get("rules"), list):
        return drbp["rules"]
    return None


def find_raw_counts(obj, path=""):
    """Search the JSON tree for a dict holding explicit tp/fp/fn counts."""
    if isinstance(obj, dict):
        lowered = {str(k).lower() for k in obj.keys()}
        if {"tp", "fp", "fn"} <= lowered:
            return obj, path
        for key, val in obj.items():
            found = find_raw_counts(val, f"{path}.{key}")
            if found is not None:
                return found
    elif isinstance(obj, list):
        for idx, val in enumerate(obj):
            found = find_raw_counts(val, f"{path}[{idx}]")
            if found is not None:
                return found
    return None


def locate_results_file(preferred: Path):
    """Return (path, data) of an evaluation file that contains rule results."""
    candidates = []
    if preferred is not None:
        candidates.append(preferred)
    directory = (preferred or DEFAULT_FILE).parent
    candidates.extend(sorted(directory.glob("evaluation*.json")))
    seen = set()
    for path in candidates:
        if path in seen or not path.exists():
            continue
        seen.add(path)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if find_rules_key(data) is not None:
            return path, data
    return None, None


def prf(tp: int, fp: int, fn: int):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def count_from_cases(rules, threshold: float):
    tp = fp = fn = tn = 0
    for case in rules:
        expert = str(case.get("expert", "")).strip()
        prediction = str(case.get("vis_prediction", "")).strip()
        if prediction == "":
            defects = case.get("defects") or case.get("defects_raw") or []
            prediction = POSITIVE if len(defects) > 0 else "NO_DEFECT"

        expert_defect = expert == POSITIVE
        pred_defect = prediction == POSITIVE
        if pred_defect and threshold > 0.0:
            conf = float(case.get(CONFIDENCE_FIELD, 0.0) or 0.0)
            pred_defect = conf >= threshold

        if pred_defect and expert_defect:
            tp += 1
        elif pred_defect and not expert_defect:
            fp += 1
        elif not pred_defect and expert_defect:
            fn += 1
        else:
            tn += 1
    return tp, fp, fn, tn


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Extract Precision/Recall/F1 from the rule-based results in an evaluation JSON."
    )
    parser.add_argument(
        "--file",
        default=str(DEFAULT_FILE),
        help="Path to the evaluation JSON (default: backend/evaluation_results_groq-gpt-oss-120b_run3.json)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum confidence for a predicted defect to count (0.0 = no threshold; use 0.70 for BR-10)",
    )
    args = parser.parse_args(argv)

    preferred = Path(args.file)
    if not preferred.is_absolute():
        preferred = REPO_ROOT / preferred

    path, data = locate_results_file(preferred)
    if data is None:
        where = f"'{preferred}'" if preferred != DEFAULT_FILE else str(DEFAULT_FILE)
        raise SystemExit(
            f"❌ No evaluation file with rule-based ('rules') results found (checked {where}"
            f" and siblings in {preferred.parent})."
        )

    rules = find_rules_key(data)
    n_cases = len(rules) if isinstance(rules, list) else 0

    # 1) Prefer explicit raw counts if the JSON stores them.
    counts_hit = find_raw_counts(data)
    if counts_hit is not None:
        counts, where = counts_hit
        tp = int(counts.get("tp", counts.get("TP", 0)))
        fp = int(counts.get("fp", counts.get("FP", 0)))
        fn = int(counts.get("fn", counts.get("FN", 0)))
        tn = int(counts.get("tn", counts.get("TN", 0)))
        source = f"raw counts found at '{where}'"
    else:
        # 2) Otherwise compute TP/FP/FN/TN by comparing expert vs vis_prediction.
        tp, fp, fn, tn = count_from_cases(rules, args.threshold)
        setting = f"threshold={args.threshold:g}" if args.threshold > 0 else "no threshold"
        source = f"per-case comparison (expert vs vis_prediction), {setting}"

    precision, recall, f1 = prf(tp, fp, fn)

    print(f"📄 Evaluation file : {path}")
    print(f"🔖 Rules cases     : {n_cases}")
    print(f"📊 Count source    : {source}")
    print(f"   TP = {tp}, FP = {fp}, FN = {fn}, TN = {tn}")
    print()
    print(f"   Precision = TP / (TP + FP) = {tp} / ({tp} + {fp}) = {precision:.3f}")
    print(f"   Recall    = TP / (TP + FN) = {tp} / ({tp} + {fn}) = {recall:.3f}")
    print(f"   F1-score  = 2·P·R / (P + R)  = {f1:.3f}")
    print()
    print(f"✅ Precision = {precision:.3f}   Recall = {recall:.3f}   F1 = {f1:.3f}")
    print("   (copy these decimal values into your paper's table)")


if __name__ == "__main__":
    main()