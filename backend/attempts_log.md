# Evaluation Attempts Log

Every attempt to obtain a frozen held-out evaluation result, in order, with
its outcome. **Only runs with `status == COMPLETE` contribute numbers to the
paper.** A run with any failed LLM call is `INCOMPLETE` and is never reported
as a result: a failed call is not a "no defect" verdict.

Dataset for every attempt: `backend/test_data/held_out_test_set.json`
(n = 36, split seed 42). Frozen configuration: model
`openai/gpt-oss-120b` via Groq, prompt `backend/services/ai/prompts_v3.txt`
(SHA-256 `071c2fcc…a1a47`), temperature 0.1, hybrid mode `llm_first`,
reported confidence threshold 0.90, reasoning effort `low`, max tokens 4096.
Freeze commit: `836f443` (tag `pre-test-freeze`).

## Summary

| # | Provider / profile | Model | Status | LLM answered | Outcome |
|---|---|---|---|---|---|
| 1 | OVHcloud AI Endpoints (`ovh-llama33-70b`) | `Meta-Llama-3_3-70B-Instruct` | **NOT COMPLETED** | 0/36 | HTTP 403 on the anonymous tier — attempt abandoned, **not reported** |
| 2 | Groq (`groq-gpt-oss-120b`) — run 1 | `openai/gpt-oss-120b` | COMPLETE (superseded) | 36/36 | Produced with the pre-refactor two-call harness; **excluded from the reported results** (see "Harness change" below) |
| 3 | Groq (`groq-gpt-oss-120b`) — run 2 | `openai/gpt-oss-120b` | **INCOMPLETE** | 30/36 | Infrastructure failures only (HTTP 429 ×2, DNS/network ×8). First attempt of this run hit ~15 HTTP 429s and was overwritten by the permitted rerun. Not reported |
| 4 | Groq (`groq-gpt-oss-120b`) — run 3 | `openai/gpt-oss-120b` | **COMPLETE** | 36/36 | **Reported** — first run under the one-call harness |
| 5 | Groq (`groq-gpt-oss-120b`) — run 4 | `openai/gpt-oss-120b` | **COMPLETE** | 36/36 | **Reported** — second one-call replicate (stability + mean±SD) |

## Harness change between run 1 and run 3 (important for the paper)

The evaluation driver `scripts/run_frozen_eval.py` was refactored so that a
**single provider call per case feeds both the LLM-only and the HYBRID path**
(the frozen `Validator(mode="llm_first")` logic is applied to that one result
instead of the provider being called twice). The frozen artifacts were not
modified: the prompt file, the SHA-256 assertion, temperature, mode and
threshold are unchanged, and the refactor was verified to be *logically
equivalent* to the frozen `Validator` on all 36 cases
(`/tmp/verify_equiv_offline.py`: 0 mismatches, 0/36 differences between the
refactored logic and the frozen `Validator` logic applied to the same
recorded result).

Consequences for the recorded runs:

- **Run 1** (and run 2) were produced by the earlier **two-call** harness: the
  LLM-only and HYBRID paths came from *two independent provider calls* per
  case, so they can differ from each other. Measured on run 1: 21/36 cases
  have a different defect set between the two paths; the summed per-path
  latency differs (171,452 ms vs 201,218 ms), confirming two separate calls.
- **Run 3** and later were produced by the **one-call** harness: 0/36 cases
  differ between the paths and the summed per-path latency is identical
  (46,761 ms for both), confirming one shared call.

Because the frozen protocol requires one provider call per case, **run 1 is
not comparable to run 3** and is therefore excluded from the reported
metrics, stability estimates and McNemar comparisons. It is retained in the
repository as a historical artifact only. This is a deviation from the
"3 runs per profile" plan and is stated explicitly as a limitation.

<!-- SECTION:DETAILS -->

## Attempt details

### OVHcloud — `ovh-llama33-70b` (attempted, NOT completed)

- Endpoint: `https://oai.endpoints.kepler.ai.cloud.ovh.net/v1` (anonymous tier).
- Result: every request returned **HTTP 403 Forbidden**; a minority of
  requests failed earlier with DNS resolution errors
  (`Failed to resolve 'oai.endpoints.kepler.ai.cloud.ovh.net'`).
- 113 of the 114 provider error lines in the log are 403 responses; the
  remaining one is the DNS failure.
- The 403 detector (`_is_auth_failure` in `scripts/run_frozen_eval.py`) was
  validated against these real log lines: all 403 lines are detected as
  terminal auth failures and the DNS line is not.
- Log: `backend/logs/ovh_run1_403.log`.
- **Outcome: attempted but not completed. No OVH metrics are reported in the
  paper, and OVH is not used as a second profile.**

### Groq run 1 — COMPLETE but superseded (harness difference)

- `backend/evaluation_results_groq-gpt-oss-120b_run1.json`
- 2026-10-20T05:44:01Z, 36/36 LLM answered, inter-case delay 2.5 s.
- Produced with the two-call harness → excluded from reported metrics.

### Groq run 2 — INCOMPLETE (infrastructure only)

- File: `backend/evaluation_results_groq-gpt-oss-120b_run2_INCOMPLETE.json`
  (renamed from `…_run2.json` so it can never be mistaken for a usable run).
- 2026-10-20T16:12:35Z, inter-case delay 25 s, 30/36 LLM answered.
- Failure classification: **HTTP 429 ×2, other (DNS/network) ×8**.
- Every failure was classified as an infrastructure problem. There were **no**
  empty, cut-off, JSON-parse or model-mismatch failures — i.e. no case failed
  because of the model's output.
- The first attempt at this run (same settings) was overwritten by the
  permitted rerun; its log recorded roughly 15 HTTP 429 responses.
- **Outcome: not reported.** No LLM/HYBRID metric from this run appears in
  the paper.

### Groq run 3 — COMPLETE (reported)

- File: `backend/evaluation_results_groq-gpt-oss-120b_run3.json`
- 2026-10-21T12:11:30Z, 36/36 LLM answered, inter-case delay 25 s,
  0 HTTP 429, 0 other failures.
- First run under the one-call harness (0/36 LLM-vs-HYBRID differences).
- Log: `/tmp/groq_run3.log`.
- **Outcome: reported.** Contributes the headline metrics, the per-category
  tables, the threshold sweep and (with run 4) the stability estimate.

### Groq run 4 — COMPLETE (reported)

- File: `backend/evaluation_results_groq-gpt-oss-120b_run4.json`
- 2026-10-21T13:11:08Z, 36/36 LLM answered, inter-case delay 25 s,
  0 HTTP 429, 0 other failures.
- Second run under the one-call harness (0/36 LLM-vs-HYBRID differences;
  summed per-path latency identical at 48,113 ms).
- Log: `/tmp/groq_run4.log`.
- **Outcome: reported.** Together with run 3 it provides the per-case
  stability estimate (0.778 at threshold 0.90, 0.861 at 0.70) and the
  mean ± SD across complete runs.

## Honesty rules applied throughout

1. A failed / empty / cut-off / model-mismatched provider call is recorded as
   `llm_failed` and **never** as a verdict.
2. Any run containing a failed call is marked `INCOMPLETE` and is excluded
   from all reported metrics.
3. HTTP 401/403 are terminal, not transient: the driver aborts after three
   consecutive occurrences, exits non-zero, records `INCOMPLETE`, and prints
   the sanitized status and response body (secret-looking tokens redacted).
   Covered by `tests/unit/test_auth_abort_main.py`.
4. A failed LLM call never inherits the rules-based verdict: the LLM-only
   path records `NO_DEFECT` with `llm_failed = true` (not a false positive).
5. `scripts/08_final_report.py` only reads runs whose `status == "COMPLETE"`;
   every other file it is given is listed as skipped and contributes nothing.
