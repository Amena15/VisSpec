# Evaluation Dataset — Provenance & Codebook

> **Integrity notice.** `dev_set.json` and `held_out_test_set.json` are a frozen
> stratified split of `test_dataset.json` produced by `split_dataset.py`
> (**seed = 42**). Rules, prompts, and thresholds were tuned on `dev_set.json`
> **only**; `held_out_test_set.json` must never be edited or used for tuning
> after the first test run. If the held-out file is modified, the split (and
> every reported metric) is invalidated.

## Files

| File | Cases | Purpose |
|---|---|---|
| `test_dataset.json` | 104 | Master dataset (source of the split) |
| `dev_set.json` | 68 | Development set — rule/prompt tuning only |
| `held_out_test_set.json` | 36 | Held-out test set — final evaluation only |

## Category counts (full dataset, N = 104)

| expert_verdict | defect_type | n | % |
|---|---|---|---|
| DEFECT | ambiguity | 44 | 42.3% |
| DEFECT | inconsistency | 6 | 5.8% |
| DEFECT | incomplete | 2 | 1.9% |
| DEFECT | unverifiable | 2 | 1.9% |
| NO_DEFECT | — | 50 | 48.1% |

Held-out split (N = 36): ambiguity 15, inconsistency 2, incomplete 1,
unverifiable 1, non-defective 17.

**Known limitation:** categories with < 10 cases (incomplete, unverifiable,
inconsistency) are too small for reliable per-category estimates. They are
reported for completeness only; no conclusion should be drawn from them.
Adding ≥ 30 blind-labelled cases per category is future work.

## Case schema

```json
{
  "id": "TC-002",
  "text": "The system must respond within 200 milliseconds.",
  "expert_verdict": "NO_DEFECT",
  "defect_type": null
}
```

- `expert_verdict`: `"DEFECT"` or `"NO_DEFECT"`.
- `defect_type`: one of `ambiguity`, `incompleteness`, `inconsistency`,
  `unverifiable` (null for non-defective). Note: some files use the short
  label `incomplete`; evaluation scripts normalise both to `incomplete`.

## Codebook (defect definitions)

Aligned with IEEE 830-1998 quality attributes and ISO/IEC/IEEE 29148
requirement-statement criteria:

| Category | Definition used for labelling |
|---|---|
| ambiguity | Vague or subjective terms (e.g. "fast", "adequate", "user-friendly") with multiple plausible interpretations, or unclear pronoun references |
| incompleteness | Missing conditions, exceptions, error handling, constraints, or a missing modal verb / actor |
| inconsistency | Contradiction within the statement or with standard requirements-engineering practice |
| unverifiable | No measurable acceptance criterion or test condition |

## Annotation procedure — TO BE FILLED

- **Annotators:** TO BE FILLED (number, roles, years of experience — describe
  what actually happened; do not claim "three experts" unless true).
- **Process:** TO BE FILLED (independent labelling? written codebook version?
  disagreement resolution method?).
- **Inter-rater agreement:** NOT YET COMPUTED. `gold_labels_SYNTHETIC_TEST.csv`
  in the repository root is a **synthetic test fixture** for
  `scripts/02_interrater_kappa.py` (rows "txt a"…), NOT real annotations, and
  must never be reported as agreement evidence. Real agreement (Fleiss' κ)
  requires the original independent labels; if those no longer exist, ask two
  colleagues to blind-label the shuffled list and compute κ from their labels.

## Provenance — TO BE FILLED

- **Case authorship:** TO BE FILLED (who wrote/adapted the 104 cases, from
  which source documents, under what licence, and whether any confidential
  industrial SRS content is included).
