"""
Frozen-configuration evaluation driver (protocol step 5). NEW FILE — modifies
nothing frozen. Uses only frozen APIs as specified in FREEZE.md:
    prompt  = backend/services/ai/prompts_v3.txt  (SHA-256 asserted at runtime)
    temp    = 0.1, mode = llm_first, profile from env LLM_PROFILE
Paths per run: RULES (Validator use_llm=False), LLM-only (v3 LLMValidator
direct), HYBRID (llm_first: LLM defects if usable, else rules fallback).
A SINGLE LLM call per case feeds both LLM-only and HYBRID — the provider is
hit once per case instead of twice. The frozen Validator default prompt is v2,
so the driver uses the frozen v3 instance directly (no code edits to frozen
files).

Honesty rules (unchanged): a failed / empty / cut-off / model-mismatched call
is llm_failed, never a verdict. Any llm_failed -> run status INCOMPLETE.

Usage:
    python3 scripts/run_frozen_eval.py --profile groq-gpt-oss-120b \
        --run 1 --dataset backend/test_data/held_out_test_set.json [--delay 2.5]
    LLM_PROFILE=ovh-llama33-70b python3 scripts/run_frozen_eval.py \
        --profile ovh-llama33-70b --run 1 --delay 15.0 ...
Exit codes: 0 COMPLETE, 2 INCOMPLETE (failures; inspect classification),
            1 harness/config error.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

FROZEN_PROMPT = REPO / "backend" / "services" / "ai" / "prompts_v3.txt"
# From FREEZE.md — abort if the artifact on disk differs.
FROZEN_PROMPT_SHA256 = "071c2fcc9f5d1b8f53d98a509e475af3b4ac148e8dcd1d73f8a32a10f2ba1a47"
FROZEN_TEMPERATURE = 0.1
FROZEN_MODE = "llm_first"
SPLIT_SEED = 42


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                              text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def _compact(defects):
    return [{"type": d.get("type"), "confidence": d.get("confidence"),
             "evidence": d.get("evidence"),
             "description": (d.get("description") or "")[:120]}
            for d in defects]


def _type_counts(defects):
    counts = {}
    for d in defects:
        t = d.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


def _redact_keys(text: str) -> str:
    """Redact secret-looking tokens (bearer tokens, API keys) from a string
    before it is printed/logged. Never print raw keys."""
    import re
    text = re.sub(r"(?i)(authorization:\s*)bearer\s*\S+", r"\1REDACTED", text)
    text = re.sub(r"(?i)(api[_-]?key\s*[:=]\s*)\S+", r"\1REDACTED", text)
    # Provider key prefixes: sk-..., sk_..., gsk_..., gsk-..., xai-...
    text = re.sub(r"\b(?:gsk|sk|xai|grok)[_-][A-Za-z0-9]{8,}\b", "REDACTED", text)
    text = re.sub(r"\b[A-Za-z0-9]{32,}\b", "REDACTED", text)   # long hex tokens
    return text


def _is_auth_failure(err_text: str) -> bool:
    """True if the error string indicates a terminal HTTP 401/403."""
    if not err_text:
        return False
    return ("401" in err_text) or ("403" in err_text)


def _case(text, validator_llm, rules_validator):
    """Run one requirement through the three paths using ONE LLM call.

    The single LLM call (validator_llm.validate_requirement) feeds both the
    LLM-only path and the HYBRID (llm_first) path, so the provider is hit once
    per case instead of twice. Honesty rules are unchanged: a failed / empty /
    cut-off / model-mismatched call is llm_failed, never a verdict.
    """
    out = {}
    # Path 1: RULES (no LLM)
    t0 = time.time()
    r = rules_validator.validate_text(text)
    rules_defects = r.get("raw_defects", r.get("defects", []))
    out["rules"] = {
        "defects_raw": rules_defects,
        "llm_used": False, "llm_failed": False, "model_returned": None,
        "json_parse_ok": None, "error": None,
        "elapsed_ms": round((time.time() - t0) * 1000, 1),
    }

    # Paths 2+3: ONE LLM call shared by LLM-only and HYBRID (llm_first).
    t0 = time.time()
    llm_r = None
    llm_error = None
    is_auth_failure = False  # HTTP 401/403 — terminal config error, not transient
    try:
        llm_r = validator_llm.validate_requirement(text)
    except Exception as e:
        llm_error = str(e)
        is_auth_failure = _is_auth_failure(llm_error)
        if is_auth_failure:
            body = ""
            try:
                resp = getattr(e, "response", None)
                if resp is not None:
                    body = getattr(resp, "text", "") or ""
            except Exception:
                body = ""
            if body:
                print(f"  [AUTH-FAILURE body] {_redact_keys(body)}", flush=True)
            else:
                print(f"  [AUTH-FAILURE] {_redact_keys(llm_error)}", flush=True)
        llm_r = {"defects": [], "filtered_defects": [], "llm_used": False,
                 "json_parse_ok": False, "model_returned": None,
                 "error": llm_error}
    llm_elapsed = round((time.time() - t0) * 1000, 1)
    llm_used = bool(llm_r.get("llm_used"))
    json_ok = bool(llm_r.get("json_parse_ok", False))
    llm_ok = llm_used and json_ok
    llm_failed = not llm_ok
    llm_defects_raw = llm_r.get("defects", [])
    # BR-10 enforced list (production pipeline uses filtered_defects).
    llm_defects = llm_r.get("filtered_defects") or llm_defects_raw

    # LLM-only path (raw defects, unchanged semantics).
    out["llm"] = {
        "defects_raw": llm_defects_raw,
        "llm_used": llm_used,
        "llm_failed": llm_failed,
        "model_returned": llm_r.get("model_returned"),
        "json_parse_ok": json_ok,
        "error": llm_r.get("error"),
        "elapsed_ms": llm_elapsed,
    }

    # HYBRID (llm_first): LLM defects if usable, else fall back to rules.
    # Mirrors Validator(use_llm=True, mode="llm_first").
    if llm_ok and llm_defects:
        hybrid_defects = llm_defects
        hybrid_error = None
    else:
        hybrid_defects = rules_defects
        hybrid_error = llm_r.get("error") if llm_failed else None

    out["hybrid"] = {
        "defects_raw": hybrid_defects,
        "llm_used": llm_used,
        "llm_failed": llm_failed,
        "model_returned": llm_r.get("model_returned"),
        "json_parse_ok": json_ok,
        "error": hybrid_error,
        "elapsed_ms": llm_elapsed,
    }
    return out, is_auth_failure


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--run", type=int, required=True)
    ap.add_argument("--dataset", default="backend/test_data/held_out_test_set.json")
    ap.add_argument("--delay", type=float, default=2.5,
                    help="seconds between cases (rate-limit pacing)")
    ap.add_argument("--out-dir", default="backend")
    a = ap.parse_args()

    import os
    os.environ["LLM_PROFILE"] = a.profile  # profile switch; no .env edits

    from backend.core.config import settings
    from backend.services.ai.llm_validator import LLMValidator
    from backend.services.validation.validator import Validator

    sha = hashlib.sha256(FROZEN_PROMPT.read_bytes()).hexdigest()
    if sha != FROZEN_PROMPT_SHA256:
        print(f"ABORT: frozen prompt SHA mismatch ({sha} != {FROZEN_PROMPT_SHA256})")
        return 1
    if settings.LLM_PROFILE != a.profile:
        print(f"ABORT: profile env did not take effect ({settings.LLM_PROFILE})")
        return 1

    data = json.loads((REPO / a.dataset).read_text(encoding="utf-8"))
    n = len(data)
    print("=" * 78)
    print(f"FROZEN EVAL — profile={a.profile} run={a.run} n={n}")
    print(f"model={settings.llm_model_id} host={settings.llm_host} "
          f"temp={FROZEN_TEMPERATURE} prompt_sha={sha[:12]} mode={FROZEN_MODE}")
    print("=" * 78)

    v3 = LLMValidator(prompt_path=str(FROZEN_PROMPT), temperature=FROZEN_TEMPERATURE)
    if not v3.is_available:
        print("ABORT: profile unavailable")
        return 1
    rules_v = Validator(use_llm=False)
    # HYBRID (llm_first) is derived from the single LLM call inside _case;
    # no separate Validator instance / second LLM call is needed.

    per_case, failed_429, failed_other = [], 0, 0
    consecutive_auth_failures = 0  # 401/403 are terminal, not transient
    auth_aborted = False
    for i, item in enumerate(data, 1):
        if i > 1 and a.delay:
            time.sleep(a.delay)
        paths, is_auth_failure = _case(item["text"], v3, rules_v)
        # One LLM call serves both llm+hybrid, so count a failure once per case.
        if paths["llm"]["llm_failed"]:
            err = (paths["llm"]["error"] or "")
            if "429" in err:
                failed_429 += 1
            else:
                failed_other += 1
        rec = {"id": item["id"],
               "text": item["text"][:70] + ("..." if len(item["text"]) > 70 else ""),
               "expert": item["expert_verdict"],
               "expert_defect_type": item.get("defect_type")}
        for path, o in paths.items():
            conf = max([float(d.get("confidence", 0.0))
                        for d in o["defects_raw"]], default=0.0)
            rec[path] = {
                "vis_prediction": "DEFECT" if o["defects_raw"] else "NO_DEFECT",
                "confidence": round(conf, 3),
                "defect_type_counts": _type_counts(o["defects_raw"]),
                "defects_raw": _compact(o["defects_raw"]),
                "llm_used": o["llm_used"], "llm_failed": o["llm_failed"],
                "model_returned": o["model_returned"],
                "json_parse_ok": o["json_parse_ok"], "error": o["error"],
                "elapsed_ms": o["elapsed_ms"],
            }
        # Record EVERY attempted case before the abort check, so the aborting
        # case is not silently dropped from the persisted results.
        per_case.append(rec)
        mark = (" [LLM-FAILED]" if any(paths[p]["llm_failed"]
                for p in ("llm", "hybrid")) else "")
        print(f"[{i:02d}/{n}] {item['id']}{mark}", flush=True)
        # 401/403 are terminal configuration errors (not rate limits): abort
        # after 3 consecutive; the response body (keys redacted) was already
        # printed by _case. Do not retry with different settings.
        if is_auth_failure:
            consecutive_auth_failures += 1
            if consecutive_auth_failures >= 3:
                print(f"ABORT: 3 consecutive 401/403 responses on profile "
                      f"{a.profile}; stopping run {a.run}.", flush=True)
                auth_aborted = True
                break
        else:
            consecutive_auth_failures = 0

    answered = {p: sum(1 for r in per_case if r[p]["llm_used"])
                for p in ("llm", "hybrid")}
    print(f"\nLLM answered — llm-only: {answered['llm']}/{n}, "
          f"hybrid: {answered['hybrid']}/{n}")
    incomplete = (failed_429 + failed_other) > 0
    status = "INCOMPLETE" if incomplete else "COMPLETE"
    print(f"status: {status} (429-failures={failed_429}, "
          f"other-failures={failed_other})")

    prov = {
        "git_commit": git("rev-parse", "HEAD"),
        "git_tag": git("describe", "--tags", "--exact-match"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "profile": a.profile,
        "model_configured": settings.llm_model_id,
        "model_returned_unique": sorted({r[p]["model_returned"]
                                         for r in per_case
                                         for p in ("llm", "hybrid")
                                         if r[p]["model_returned"]}),
        "endpoint_host": settings.llm_host,
        "temperature": FROZEN_TEMPERATURE,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "reasoning_effort": settings.LLM_REASONING_EFFORT,
        "prompt_file": "backend/services/ai/prompts_v3.txt",
        "prompt_sha256": sha,
        "hybrid_mode": FROZEN_MODE,
        "split_seed": SPLIT_SEED,
        "dataset": a.dataset,
        "dataset_size": n,
        "inter_case_delay_s": a.delay,
        "run": a.run,
        "llm_answered": answered,
        "failure_classification": {"http_429": failed_429, "other": failed_other},
        "auth_aborted": auth_aborted,
        "cases_attempted": len(per_case),
    }
    result = {
        "status": status,
        "status_note": ("Some required LLM call failed. LLM/Hybrid metrics are "
                        "NOT valid LLM results for this run." if incomplete else
                        "All required LLM calls answered."),
        "provenance": prov,
        "detailed_results_by_path": {
            path: [{**{k: r[k] for k in ("id", "text", "expert",
                                         "expert_defect_type")},
                    **r[path]} for r in per_case]
            for path in ("rules", "llm", "hybrid")
        },
        # script 01 compatibility: headline path = hybrid
        "detailed_results": [{**{k: r[k] for k in ("id", "text", "expert",
                                                   "expert_defect_type")},
                              **r["hybrid"]} for r in per_case],
    }
    out = REPO / a.out_dir / f"evaluation_results_{a.profile}_run{a.run}.json"
    out.write_text(json.dumps(result, indent=1), encoding="utf-8")
    try:
        shown = out.relative_to(REPO)
    except ValueError:
        shown = out  # --out-dir may point outside the repo
    print(f"saved: {shown}")
    return 2 if incomplete else 0


if __name__ == "__main__":
    sys.exit(main())

