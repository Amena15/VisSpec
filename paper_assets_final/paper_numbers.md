# paper_numbers.md (auto-generated)

Frozen evaluation runs (reported confidence threshold 0.9).

- harness: one-call - `evaluation_results_groq-gpt-oss-120b_run3.json, evaluation_results_groq-gpt-oss-120b_run4.json` (one provider call per case)
- harness: two-call - `evaluation_results_groq-gpt-oss-120b_run1.json` (TWO provider calls per case - not comparable with one-call runs)

**WARNING: runs with different harness kinds were given together. Only the one-call runs are valid under the frozen protocol; the others are excluded below.**

## Runs used

Complete runs used: 2 | skipped (not COMPLETE): 1

- **USED** `evaluation_results_groq-gpt-oss-120b_run3.json` - run 3, 2026-10-21T12:11:30+00:00, LLM answered {'llm': 36, 'hybrid': 36}, inter-case delay 25.0s
- **USED** `evaluation_results_groq-gpt-oss-120b_run4.json` - run 4, 2026-10-21T13:11:08+00:00, LLM answered {'llm': 36, 'hybrid': 36}, inter-case delay 25.0s
- **SKIPPED (not COMPLETE)** `evaluation_results_groq-gpt-oss-120b_run2_INCOMPLETE.json` - status `INCOMPLETE`, LLM answered {'llm': 30, 'hybrid': 32}, failures {'http_429': 2, 'other': 8}. Not reported as a result.

## Table VI - frozen configuration (provenance of run 3)

| Item | Value |
|---|---|
| profile | `groq-gpt-oss-120b` |
| model_configured | `openai/gpt-oss-120b` |
| endpoint_host | `api.groq.com` |
| temperature | `0.1` |
| max_tokens | `4096` |
| reasoning_effort | `low` |
| prompt_file | `backend/services/ai/prompts_v3.txt` |
| prompt_sha256 | `071c2fcc9f5d1b8f53d98a509e475af3b4ac148e8dcd1d73f8a32a10f2ba1a47` |
| hybrid_mode | `llm_first` |
| split_seed | `42` |
| dataset | `backend/test_data/held_out_test_set.json` |
| dataset_size | `36` |
| inter_case_delay_s | `25.0` |
| git_commit | `836f44307263d2c99ac1973028214365af7498c0` |
| git_tag | `pre-test-freeze` |
| timestamp_utc | `2026-10-21T12:11:30+00:00` |
| confidence threshold (reported) | 0.9 |
| model actually returned | openai/gpt-oss-120b |

## Path: rules

### rules @ threshold frozen (0.9)

- run 3: TP/FP/FN/TN = 1/0/18/17 (n=36)
- Precision = 1.000 [95% CI 0.000, 1.000]
- Recall = 0.053 [95% CI 0.000, 0.174]
- F1 = 0.100 [95% CI 0.000, 0.296]
- across 2 complete runs: P = 1.000 +/- 0.000, R = 0.053 +/- 0.000, F1 = 0.100 +/- 0.000
- per-case output stability (identical verdict AND type in all 2 runs) = 1.000

### rules @ threshold BR10_0.70 (0.7)

- run 3: TP/FP/FN/TN = 13/1/6/16 (n=36)
- Precision = 0.929 [95% CI 0.765, 1.000]
- Recall = 0.684 [95% CI 0.467, 0.889]
- F1 = 0.788 [95% CI 0.606, 0.923]
- across 2 complete runs: P = 0.929 +/- 0.000, R = 0.684 +/- 0.000, F1 = 0.788 +/- 0.000
- per-case output stability (identical verdict AND type in all 2 runs) = 1.000

### rules: per-category metrics (threshold 0.9, run 3)

| category      |   n |   TP |   FP |   FN |   precision |   recall |   recall_lo |   recall_hi |    f1 |
|:--------------|----:|-----:|-----:|-----:|------------:|---------:|------------:|------------:|------:|
| ambiguity     |  15 |    0 |    0 |   15 |           0 |      0   |       0     |       0.204 | 0     |
| incomplete    |   1 |    0 |    0 |    1 |           0 |      0   |       0     |       0.793 | 0     |
| inconsistency |   2 |    1 |    0 |    1 |           1 |      0.5 |       0.095 |       0.905 | 0.667 |
| unverifiable  |   1 |    0 |    0 |    1 |           0 |      0   |       0     |       0.793 | 0     |

Macro-F1 over the 4 categories = 0.167

## Path: llm

### llm @ threshold frozen (0.9)

- run 3: TP/FP/FN/TN = 18/7/1/10 (n=36)
- Precision = 0.720 [95% CI 0.542, 0.889]
- Recall = 0.947 [95% CI 0.824, 1.000]
- F1 = 0.818 [95% CI 0.682, 0.926]
- across 2 complete runs: P = 0.740 +/- 0.028, R = 0.974 +/- 0.037, F1 = 0.841 +/- 0.032
- per-case output stability (identical verdict AND type in all 2 runs) = 0.778

### llm @ threshold BR10_0.70 (0.7)

- run 3: TP/FP/FN/TN = 19/11/0/6 (n=36)
- Precision = 0.633 [95% CI 0.462, 0.794]
- Recall = 1.000 [95% CI 1.000, 1.000]
- F1 = 0.776 [95% CI 0.632, 0.885]
- across 2 complete runs: P = 0.633 +/- 0.000, R = 1.000 +/- 0.000, F1 = 0.776 +/- 0.000
- per-case output stability (identical verdict AND type in all 2 runs) = 0.861

### llm: per-category metrics (threshold 0.9, run 3)

| category      |   n |   TP |   FP |   FN |   precision |   recall |   recall_lo |   recall_hi |    f1 |
|:--------------|----:|-----:|-----:|-----:|------------:|---------:|------------:|------------:|------:|
| ambiguity     |  15 |   15 |    4 |    0 |       0.789 |        1 |       0.796 |       1     | 0.882 |
| incomplete    |   1 |    0 |    6 |    1 |       0     |        0 |       0     |       0.793 | 0     |
| inconsistency |   2 |    0 |    0 |    2 |       0     |        0 |       0     |       0.658 | 0     |
| unverifiable  |   1 |    0 |    0 |    1 |       0     |        0 |       0     |       0.793 | 0     |

Macro-F1 over the 4 categories = 0.221

## Path: hybrid

### hybrid @ threshold frozen (0.9)

- run 3: TP/FP/FN/TN = 18/7/1/10 (n=36)
- Precision = 0.720 [95% CI 0.536, 0.889]
- Recall = 0.947 [95% CI 0.818, 1.000]
- F1 = 0.818 [95% CI 0.667, 0.927]
- across 2 complete runs: P = 0.740 +/- 0.028, R = 0.974 +/- 0.037, F1 = 0.841 +/- 0.032
- per-case output stability (identical verdict AND type in all 2 runs) = 0.778

### hybrid @ threshold BR10_0.70 (0.7)

- run 3: TP/FP/FN/TN = 19/11/0/6 (n=36)
- Precision = 0.633 [95% CI 0.461, 0.800]
- Recall = 1.000 [95% CI 1.000, 1.000]
- F1 = 0.776 [95% CI 0.632, 0.889]
- across 2 complete runs: P = 0.633 +/- 0.000, R = 1.000 +/- 0.000, F1 = 0.776 +/- 0.000
- per-case output stability (identical verdict AND type in all 2 runs) = 0.861

### hybrid: per-category metrics (threshold 0.9, run 3)

| category      |   n |   TP |   FP |   FN |   precision |   recall |   recall_lo |   recall_hi |    f1 |
|:--------------|----:|-----:|-----:|-----:|------------:|---------:|------------:|------------:|------:|
| ambiguity     |  15 |   15 |    4 |    0 |       0.789 |        1 |       0.796 |       1     | 0.882 |
| incomplete    |   1 |    0 |    6 |    1 |       0     |        0 |       0     |       0.793 | 0     |
| inconsistency |   2 |    0 |    0 |    2 |       0     |        0 |       0     |       0.658 | 0     |
| unverifiable  |   1 |    0 |    0 |    1 |       0     |        0 |       0     |       0.793 | 0     |

Macro-F1 over the 4 categories = 0.221

## Category-level detection vs. correct labelling (run 3, threshold 0.9, LLM path)

Binary recall counts a case as found when *any* defect is reported. This table separates 'flagged as a defect' from 'flagged with the correct category'.

- run 3: non-ambiguity defective cases = 4, flagged as a defect = 3, flagged with the CORRECT category = 2, missed entirely = 1 (TC-055)
  - false positives by predicted type: {'incomplete': 6, 'ambiguity': 1}
- run 4: non-ambiguity defective cases = 4, flagged as a defect = 4, flagged with the CORRECT category = 2, missed entirely = 0
  - false positives by predicted type: {'incomplete': 3, 'ambiguity': 2, 'unverifiable': 1}

## Latency

Per-case provider latency recorded by the driver (`elapsed_ms`). In the one-call harness the LLM-only and HYBRID paths share one call, so the two paths report the same latency by construction.

| path   |   n_calls |   mean_ms |   median_ms |   p95_ms |   min_ms |   max_ms |
|:-------|----------:|----------:|------------:|---------:|---------:|---------:|
| rules  |        72 |       1.2 |         0.8 |      3.7 |      0.1 |      5.1 |
| llm    |        72 |    1317.7 |      1361.5 |   1860   |    546.3 |   2012.5 |
| hybrid |        72 |    1317.7 |      1361.5 |   1860   |    546.3 |   2012.5 |


## Paired comparison (run 3, threshold 0.9) - McNemar exact test on correct/incorrect verdict
- rules vs llm: only rules correct = 8, only llm correct = 18, McNemar exact p = 0.076
- rules vs hybrid: only rules correct = 8, only hybrid correct = 18, McNemar exact p = 0.076
- llm vs hybrid: only llm correct = 0, only hybrid correct = 0, McNemar exact p = 1.000