"""
Dev-only prompt / temperature / hybrid-mode / threshold tuning (protocol step 4).

STRICTLY dev_set.json (68 cases). The held-out test set is never loaded here.

Grid:
  prompts   : prompts_v2.txt (incumbent) vs prompts_v3.txt (few-shot anchors)
  temp      : 0.1 vs 0.0
  modes     : llm_first vs union (simulated from cached raw outputs; rules are
              deterministic, so simulation == production hybrid by construction,
              and an equivalence spot-check against the real Validator is run)
  threshold : {0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90}

Protocol:
  - 5-fold CV on the dev set (seed 42): P/R/F1 per fold, mean +/- SD.
  - Every run appends to backend/experiments_dev.md with full provenance.
  - Selection rule (declared in advance): maximize mean fold F1; ties broken
    by higher precision, then lower threshold, then the incumbent prompt.
    NO held-out data is consulted.

Run: python3 scripts/dev_prompt_tuning.py [--skip-llm]
"""
import argparse
import hashlib
import json
import random
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.core.config import settings
from backend.services.ai.llm_validator import LLMValidator
from backend.services.validation.validator import Validator

DEV_PATH = REPO_ROOT / "backend" / "test_data" / "dev_set.json"
HELD_OUT_PATH = REPO_ROOT / "backend" / "test_data" / "held_out_test_set.json"
LOG_PATH = REPO_ROOT / "backend" / "experiments_dev.md"
PROMPTS = {
    "v2": REPO_ROOT / "backend" / "services" / "ai" / "prompts_v2.txt",
    "v3": REPO_ROOT / "backend" / "services" / "ai" / "prompts_v3.txt",
}
TEMPERATURES = [0.1, 0.0]
THRESHOLDS = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90]
FOLDS = 5
SEED = 42
INTER_CALL_DELAY_S = 0.75   # Groq free-tier pacing; 429s also handled by retry


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=10,
        ).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def load_dev():
    """Load dev set; hard-fail if anything points at the held-out file."""
    if DEV_PATH.resolve() == HELD_OUT_PATH.resolve():
        raise RuntimeError("Refusing to tune on the held-out test set.")
    data = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    assert len(data) == 68, f"dev set should be 68 cases, got {len(data)}"
    return data


def prf(cases, verdict_fn, threshold):
    """P/R/F1 for binary defect detection at a threshold."""
    tp = fp = fn = tn = 0
    for c in cases:
        pred = verdict_fn(c, threshold)
        gold = c["expert_verdict"] == "DEFECT"
        if pred and gold: tp += 1
        elif pred and not gold: fp += 1
        elif not pred and gold: fn += 1
        else: tn += 1
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"p": p, "r": r, "f1": f1, "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def fold_split(cases, folds=FOLDS, seed=SEED):
    rng = random.Random(seed)
    idx = list(range(len(cases)))
    rng.shuffle(idx)
    size = len(idx) // folds
    out, start = [], 0
    for k in range(folds):
        end = start + size + (1 if k < len(idx) % folds else 0)
        out.append([cases[i] for i in idx[start:end]])
        start = end
    return out


def run_config(dev, prompt_name, temperature, log_lines):
    """Call the LLM once per dev case; returns per-case raw results."""
    v = LLMValidator(prompt_path=str(PROMPTS[prompt_name]), temperature=temperature)
    assert v.is_available, "LLM unavailable"
    results, answered, failed = [], 0, 0
    print(f"  [{prompt_name} @ {temperature}] 68 calls ...", flush=True)
    for i, c in enumerate(dev, 1):
        if i > 1:
            time.sleep(INTER_CALL_DELAY_S)
        t0 = time.time()
        r = v.validate_requirement(c["text"])
        elapsed = round((time.time() - t0) * 1000, 1)
        ok = bool(r.get("llm_used")) and bool(r.get("json_parse_ok"))
        if ok:
            answered += 1
        else:
            failed += 1
        results.append({
            "id": c["id"],
            "llm_used": ok,
            "model_returned": r.get("model_returned"),
            "error": r.get("error"),
            "defects": r.get("defects", []),   # RAW (pre-threshold)
            "elapsed_ms": elapsed,
        })
        if i % 17 == 0:
            print(f"      {i}/68 (answered={answered} failed={failed})", flush=True)
    n_mismatch = sum(
        1 for x in results
        if x["model_returned"] and x["model_returned"] != v.model
    )
    log_lines.append(
        f"| {prompt_name} | {temperature} | {answered} | {failed} | "
        f"{n_mismatch} | {v.prompt_sha256[:12]} |"
    )
    return results, answered, failed, v

def defects_at(defects, th):
    return [d for d in defects if float(d.get("confidence", 0.0)) >= th]


def make_verdict(mode, llm_results, rules_by_id):
    by_id = {x["id"]: x for x in llm_results}

    def verdict(c, th):
        llm_d = defects_at(by_id[c["id"]]["defects"], th)
        if mode == "llm_first":
            src = llm_d if llm_d else defects_at(rules_by_id[c["id"]], th)
        else:  # union
            src = llm_d + defects_at(rules_by_id[c["id"]], th)
        return len(src) > 0
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-llm", action="store_true",
                    help="Reuse cached results (no API calls)")
    args = ap.parse_args()

    dev = load_dev()
    cache_path = Path("/tmp/dev_tuning_cache.json")

    print("=" * 78)
    print("DEV-ONLY TUNING (held-out test set is NOT loaded)")
    print(f"profile={settings.LLM_PROFILE} model={settings.llm_model_id} "
          f"host={settings.llm_host}")
    print("=" * 78)

    # ---- Rules once (deterministic, local) ----
    rules_validator = Validator(use_llm=False)
    rules_by_id = {}
    for c in dev:
        r = rules_validator.validate_text(c["text"])
        rules_by_id[c["id"]] = r.get("raw_defects", r.get("defects", []))

    # ---- LLM grid: 2 prompts x 2 temperatures ----
    if args.skip_llm and cache_path.exists():
        cache = json.loads(cache_path.read_text())
        configs = {(c["prompt"], c["temperature"]): c["results"]
                   for c in cache["configs"]}
        print("Loaded cached LLM results (no API calls).")
    else:
        log_header = [
            "",
            f"## Run {datetime.now(timezone.utc).isoformat(timespec='seconds')} — "
            f"dev prompt/temp grid",
            f"- commit: `{git_commit()}`",
            f"- profile: `{settings.LLM_PROFILE}` model: `{settings.llm_model_id}` "
            f"host: `{settings.llm_host}`",
            f"- dataset: `dev_set.json` n={len(dev)} (held-out NOT loaded), "
            f"folds={FOLDS} seed={SEED}",
            f"- reasoning_effort: `{settings.LLM_REASONING_EFFORT or 'none'}`, "
            f"max_tokens: {settings.LLM_MAX_TOKENS}",
            "",
            "| prompt | temp | answered | failed | model_mismatch | prompt_sha256 |",
            "|---|---|---|---|---|---|",
        ]
        configs = {}
        for pname in ("v2", "v3"):
            for t in TEMPERATURES:
                results, answered, failed, vv = run_config(
                    dev, pname, t, log_header)
                if failed:
                    print(f"  !! {pname}@{t}: {failed} failed calls")
                configs[(pname, t)] = results
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not LOG_PATH.exists():
            LOG_PATH.write_text("# Dev experiments log\n", encoding="utf-8")
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(log_header) + "\n")
        cache_path.write_text(json.dumps({
            "configs": [{"prompt": k[0], "temperature": k[1], "results": v}
                        for k, v in configs.items()],
        }))


    # ---- Equivalence spot-check: simulation == real hybrid Validator ----
    from unittest.mock import patch
    spot_ok = True
    for mode in ("llm_first", "union"):
        (pname, t) = list(configs.keys())[0]
        cached = {x["id"]: x for x in configs[(pname, t)]}
        real_v = Validator(use_llm=True, mode=mode)

        def fake_validate(text, _cached=cached, _dev=dev):
            cid = next(c["id"] for c in _dev if c["text"] == text)
            raw = _cached[cid]["defects"]
            return {"defects": raw, "filtered_defects": defects_at(raw, 0.70),
                    "llm_used": _cached[cid]["llm_used"], "json_parse_ok": True,
                    "model_used": settings.llm_model_id, "error": None}

        with patch.object(real_v.llm_validator, "validate_requirement",
                          side_effect=fake_validate):
            for c in dev[:5]:
                real = real_v.validate_text(c["text"])
                real_pred = len(defects_at(
                    real.get("raw_defects", real.get("defects", [])), 0.70)) > 0
                sim_pred = make_verdict(mode, configs[(pname, t)],
                                        rules_by_id)(c, 0.70)
                if real_pred != sim_pred:
                    spot_ok = False
                    print(f"  !! sim!=real for {mode} {c['id']}")
    print(f"Simulation == production hybrid: {spot_ok}")

    # ---- 5-fold CV over configs x modes x thresholds ----
    # Honesty: a config with ANY failed call is DISQUALIFIED from selection —
    # its per-case verdicts include implicit "no defects" from failures, which
    # must never influence the choice. It is still computed and reported,
    # flagged as ineligible.
    folds = fold_split(dev)
    rows = []
    for (pname, t), results in configs.items():
        n_failed = sum(1 for x in results if not x["llm_used"])
        eligible = (n_failed == 0)
        for mode in ("llm_first", "union"):
            vf = make_verdict(mode, results, rules_by_id)
            for th in THRESHOLDS:
                fold_f1, fold_p, fold_r = [], [], []
                for f in folds:
                    m = prf(f, vf, th)
                    fold_f1.append(m["f1"])
                    fold_p.append(m["p"])
                    fold_r.append(m["r"])
                rows.append({
                    "prompt": pname, "temp": t, "mode": mode, "threshold": th,
                    "f1_mean": statistics.mean(fold_f1),
                    "f1_sd": statistics.pstdev(fold_f1),
                    "p_mean": statistics.mean(fold_p),
                    "r_mean": statistics.mean(fold_r),
                    "n_failed": n_failed,
                    "eligible": eligible,
                })
        if not eligible:
            print(f"  !! DISQUALIFIED prompt={pname} temp={t}: "
                  f"{n_failed} failed call(s) -> not selectable")

    # ---- Selection rule (declared in docstring) over ELIGIBLE rows only ----
    eligible_rows = [r for r in rows if r["eligible"]]
    if not eligible_rows:
        print("NO ELIGIBLE CONFIG (all had failed calls) — rerun after "
              "rate-limit cool-down; nothing selected.")
        return 2

    def key(r):
        return (round(r["f1_mean"], 6), round(r["p_mean"], 6),
                -r["threshold"], 0 if r["prompt"] == "v2" else 1)
    best = max(eligible_rows, key=key)

    print("\nTop 8 by mean fold F1:")
    print(f"\nTop 8 by mean fold F1 (eligible configs only):")
    print(f"{'prompt':>6} {'temp':>4} {'mode':>9} {'thr':>4} | "
          f"{'F1':>6} {'+-':>5} {'P':>6} {'R':>6}")
    for r in sorted(eligible_rows, key=key, reverse=True)[:8]:
        print(f"{r['prompt']:>6} {r['temp']:>4} {r['mode']:>9} "
              f"{r['threshold']:>4.2f} | {r['f1_mean']:>6.3f} {r['f1_sd']:>5.3f} "
              f"{r['p_mean']:>6.3f} {r['r_mean']:>6.3f}")

    print(f"\nSELECTED: prompt={best['prompt']} temp={best['temp']} "
          f"mode={best['mode']} threshold={best['threshold']} "
          f"(F1={best['f1_mean']:.3f}+-{best['f1_sd']:.3f})")

    section = [
        "",
        f"## Run {datetime.now(timezone.utc).isoformat(timespec='seconds')} — "
        f"5-fold dev grid result",
        f"- commit: `{git_commit()}`",
        f"- simulation==production hybrid spot-check: **{spot_ok}**",
        "",
        "| prompt | temp | mode | threshold | F1 mean | F1 SD | P mean | R mean | eligible |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=key, reverse=True):
        section.append(
            f"| {r['prompt']} | {r['temp']} | {r['mode']} | {r['threshold']:.2f} "
            f"| {r['f1_mean']:.3f} | {r['f1_sd']:.3f} "
            f"| {r['p_mean']:.3f} | {r['r_mean']:.3f} "
            f"| {'yes' if r['eligible'] else 'NO (' + str(r['n_failed']) + ' failed)'} |")
    section += ["", f"**SELECTED (pre-test):** prompt=`{best['prompt']}` "
                f"temp=`{best['temp']}` mode=`{best['mode']}` "
                f"threshold=`{best['threshold']}`", ""]
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(section) + "\n")

    (Path("/tmp/dev_recommendation.json")).write_text(json.dumps({
        "prompt": best["prompt"],
        "prompt_file": f"backend/services/ai/prompts_{best['prompt']}.txt",
        "prompt_sha256": sha(PROMPTS[best["prompt"]]),
        "temperature": best["temp"],
        "mode": best["mode"],
        "threshold": best["threshold"],
        "f1_mean": best["f1_mean"], "f1_sd": best["f1_sd"],
        "model": settings.llm_model_id, "profile": settings.LLM_PROFILE,
        "host": settings.llm_host,
        "spot_check_ok": spot_ok,
        "commit": git_commit(),
    }, indent=2))
    print("Recommendation written to /tmp/dev_recommendation.json")
    print(f"Grid appended to {LOG_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
