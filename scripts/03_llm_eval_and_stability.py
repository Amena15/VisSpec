#!/usr/bin/env python3
"""
03_llm_eval_and_stability.py -- Addresses R1-C4/C5, R2-M5/M6 (LLM reproducibility, stability, threshold, held-out split).
Needs an active LLM profile + network. Run it, then copy the printed numbers into the paper.

What it does
  * freezes a stratified DEV/TEST split of the benchmark (seeded) -> tune ONLY on dev, report ONLY on test
  * evaluates three configurations on the TEST split, K repeated runs each:
        RULES  : Validator(use_llm=False)
        LLM    : LLMValidator().validate_requirement()   (Groq, temperature from settings)
        HYBRID : Validator(use_llm=True)
  * logs model id, temperature, max_tokens, prompt SHA-256, threshold, date  -> "Experimental configuration" table
  * reports mean +/- SD of P/R/F1 across runs and per-case output stability (identical verdict in all K runs)
USAGE (from repo root, backend venv active, GROQ_API_KEY set):
    python scripts/03_llm_eval_and_stability.py --runs 5 --out paper_assets/llm_eval.json
"""
import argparse, json, sys, hashlib, datetime, random, collections
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.services.validation.validator import Validator
from backend.services.ai.llm_validator import LLMValidator
from backend.core.config import settings


def split(ds, seed=2026, dev_frac=0.4):
    rnd = random.Random(seed); by = collections.defaultdict(list)
    for c in ds: by[c.get("defect_type") or "none"].append(c)
    dev, test = [], []
    for k, v in by.items():
        rnd.shuffle(v); cut = max(1, int(round(len(v) * dev_frac))) if len(v) > 2 else 1
        dev += v[:cut]; test += v[cut:]
    return dev, test


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0; r = tp / (tp + fn) if tp + fn else 0
    return p, r, (2 * p * r / (p + r) if p + r else 0)


def predict(system, text, th):
    if system == "RULES":
        res = Validator(use_llm=False).validate_text(text)
    elif system == "HYBRID":
        res = Validator(use_llm=True).validate_text(text)
    else:
        res = LLMValidator().validate_requirement(text)
    d = [x for x in res.get("defects", []) if x.get("confidence", 0) >= th]      # enforce BR-10 explicitly
    types = sorted({x.get("type") for x in d})
    return bool(d), types


def main(a):
    ds = json.load(open(ROOT / "backend/test_data/test_dataset.json"))
    dev, test = split(ds)
    print(f"dev={len(dev)}  test={len(test)}  (freeze prompts/rules BEFORE looking at test results)")
    prompt_src = (ROOT / "backend/services/ai/llm_validator.py").read_text()
    cfg = dict(date=datetime.date.today().isoformat(), model=settings.llm_model_id,
               temperature=settings.LLM_TEMPERATURE,
               max_tokens=settings.LLM_MAX_TOKENS, response_format="json_object", conf_threshold=a.threshold,
               prompt_file_sha256=hashlib.sha256(prompt_src.encode()).hexdigest()[:16], runs=a.runs,
               n_dev=len(dev), n_test=len(test))
    out = dict(config=cfg, systems={})
    for system in ["RULES", "LLM", "HYBRID"]:
        runs = []; verdicts = collections.defaultdict(list)
        for k in range(a.runs if system != "RULES" else 1):
            tp = fp = fn = tn = 0
            for c in test:
                pred, types = predict(system, c["text"], a.threshold)
                gold = c["expert_verdict"] == "DEFECT"
                verdicts[c["id"]].append((pred, tuple(types)))
                tp += pred and gold; fp += pred and not gold
                fn += (not pred) and gold; tn += (not pred) and not gold
            runs.append(prf(tp, fp, fn)); print(system, "run", k + 1, [round(x, 3) for x in runs[-1]])
        arr = np.array(runs); stab = np.mean([len(set(v)) == 1 for v in verdicts.values()])
        out["systems"][system] = dict(precision=[arr[:, 0].mean(), arr[:, 0].std()],
                                      recall=[arr[:, 1].mean(), arr[:, 1].std()],
                                      f1=[arr[:, 2].mean(), arr[:, 2].std()], output_stability=stab)
        print(system, out["systems"][system])
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=2)
    print("saved", a.out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--threshold", type=float, default=0.70)
    ap.add_argument("--out", default="paper_assets/llm_eval.json")
    main(ap.parse_args())
