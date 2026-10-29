# RQ3 Stability Check

The RQ3 paired significance test could not be reproduced from retained artifacts. The per-element grounding assessment was not saved at generation time, and re-runs of the evaluation pipeline produced differing element counts with differing condition totals. RQ3 is therefore reported as an experiment that was conducted but whose quantitative results cannot be verified from retained artifacts. No p-value, direction of effect, or element count is claimed for RQ3.

Due to the non-deterministic nature of the evaluation pipeline from retained artifacts, key fields that differ across runs include: n_cases_total, excluded_case_ids, n_pairs, totals_base.generated, totals_base.unsupported, totals_enf.generated, totals_enf.unsupported, raw_count_diff sums, prop_unsupported values, and exact_p. The script must be considered non-deterministic from retained artifacts.
