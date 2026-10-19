# PRE-TEST FREEZE

**Status: FROZEN — awaiting the "pre-test freeze" commit confirmation from the
project owner. Until that commit exists, NO held-out/test evaluation may run
with these settings.**

Frozen: 2026-10-19 (dev-only tuning complete; held-out test set untouched)

## Frozen configuration

| Item | Value |
|---|---|
| Model id | `openai/gpt-oss-120b` |
| Profile | `groq-gpt-oss-120b` |
| Endpoint host | `api.groq.com` (`https://api.groq.com/openai/v1`) |
| Reasoning effort | `low` (probe-verified accepted; code falls back without it if a provider rejects it) |
| Max tokens | 4096 |
| Prompt file | `backend/services/ai/prompts_v3.txt` |
| Prompt SHA-256 | `071c2fcc9f5d1b8f53d98a509e475af3b4ac148e8dcd1d73f8a32a10f2ba1a47` |
| Temperature | 0.1 |
| Hybrid mode | `llm_first` (rules run only when the LLM produces no usable defects) |
| Confidence threshold | **0.90** (dev-selected; BR-10 production filter stays 0.70 in code — the threshold choice is reported separately, see below) |
| Split seed | 42 (`dev_set.json` 68 / `held_out_test_set.json` 36) |
| Tuning commit | `41cd014d467d09229847f3547436a22a1fca6223` (working tree changes uncommitted) |

## How the choice was made (dev set ONLY, n=68)

- Grid: prompts {v2, v3} x temperature {0.1, 0.0} x hybrid mode {llm_first,
  union} x threshold {0.50 … 0.90}; 5-fold CV (seed 42), mean fold F1.
- Full grid, provenance and per-run call accounting: `backend/experiments_dev.md`.
- Selection rule (declared in advance in `scripts/dev_prompt_tuning.py`):
  max mean fold F1; ties -> higher precision -> lower threshold -> incumbent
  prompt.
- Winner: **v3 @ 0.1, llm_first, threshold 0.90** — dev F1 = 0.809 ± 0.139
  (P = 0.699, R = 1.000).
- v3 @ 0.0 was **disqualified** (39/68 calls failed with HTTP 429 during a
  rate-limit window); a config with failed calls is never selectable — a failed
  call must not be interpreted as "no defects".
- Hybrid-mode equivalence spot-check (simulated vs the real
  `Validator(mode=...)` code path, cached LLM outputs): **identical** on all
  spot-checked cases.
- BR-10 note: the production code filter remains 0.70 (requirement BR-10);
  the dev-selected 0.90 is the *reported evaluation threshold* for headline
  metrics; the threshold-sweep table reports both.

## Second profile (for the dual-profile comparison run)

`ovh-llama33-70b` — host `oai.endpoints.kepler.ai.cloud.ovh.net`, model
`Meta-Llama-3_3-70B-Instruct`, anonymous tier (no key). Same prompt artifact
(SHA above), temperature, mode and threshold apply; only the profile changes
(`LLM_PROFILE=ovh-llama33-70b`).

## After the freeze commit

Per protocol step 5 (on the owner's explicit go-ahead only):
evaluate RULES / LLM / HYBRID on the named test file for BOTH profiles,
3 runs each, saving `evaluation_results_<profile>.json` per profile, then the
paired McNemar exact test + bootstrap CI comparison (`scripts/07_compare_profiles.py`).
