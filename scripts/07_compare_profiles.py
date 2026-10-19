"""
Paired comparison of two evaluation result files (protocol step 5).

Given per-case verdicts from the SAME test cases evaluated with two profiles
(e.g. groq-gpt-oss-120b vs ovh-llama33-70b), computes:
  - McNemar exact test (binomial) on the discordant pairs of correctness
  - bootstrap 95% CI of the accuracy (and F1) difference (paired resampling)

Run ONLY after the pre-test freeze commit, on files produced by
backend/evaluate_model.py with the frozen settings:
    python3 scripts/07_compare_profiles.py \
        backend/evaluation_results_groq-gpt-oss-120b.json \
        backend/evaluation_results_ovh-llama33-70b.json
"""
import json
import math
import random
import sys
from pathlib import Path

SEED = 42
BOOTSTRAP_N = 10000


def load_cases(path):
    """id -> (gold_is_defect, pred_is_defect) using the BR-10 view."""
    d = json.loads(Path(path).read_text())
    per_path = d.get("detailed_results_by_path", {})
    # Headline path = hybrid (fall back to llm, then rules).
    for key in ("hybrid", "llm", "rules"):
        if key in per_path:
            cases = per_path[key]
            break
    else:
        cases = d.get("detailed_results", [])
    out = {}
    for c in cases:
        gold = c["expert"] == "DEFECT"
        pred = c.get("vis_prediction_br10", c.get("vis_prediction")) == "DEFECT"
        out[c["id"]] = (gold, pred)
    return out


def mcnemar_exact(b, c):
    """Exact two-sided binomial test on discordant pairs b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    # two-sided exact p = 2 * P(X <= k), X ~ Bin(n, 0.5), capped at 1
    p = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n) * 2
    return min(1.0, p)


def f1_score(cases, preds):
    tp = fp = fn = 0
    for cid, (gold, _) in cases.items():
        pred = preds[cid]
        if pred and gold: tp += 1
        elif pred and not gold: fp += 1
        elif not pred and gold: fn += 1
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    a_path, b_path = sys.argv[1], sys.argv[2]
    A, B = load_cases(a_path), load_cases(b_path)
    common = sorted(set(A) & set(B))
    if len(common) != len(A) or len(common) != len(B):
        print(f"WARNING: case sets differ (A={len(A)} B={len(B)} "
              f"common={len(common)}); comparing common cases only.")
    print(f"Paired comparison on {len(common)} cases")
    print(f"  A = {a_path}")
    print(f"  B = {b_path}")

    a_pred = {cid: A[cid][1] for cid in common}
    b_pred = {cid: B[cid][1] for cid in common}
    cases = {cid: A[cid] for cid in common}

    # Accuracy + discordant counts
    a_correct = sum(1 for cid in common if a_pred[cid] == cases[cid][0])
    b_correct = sum(1 for cid in common if b_pred[cid] == cases[cid][0])
    n = len(common)
    # b = A correct & B wrong; c = A wrong & B correct
    b_cnt = sum(1 for cid in common
                if a_pred[cid] == cases[cid][0] and b_pred[cid] != cases[cid][0])
    c_cnt = sum(1 for cid in common
                if a_pred[cid] != cases[cid][0] and b_pred[cid] == cases[cid][0])
    p_exact = mcnemar_exact(b_cnt, c_cnt)

    print(f"\nAccuracy:  A = {a_correct}/{n} ({a_correct/n:.3f})   "
          f"B = {b_correct}/{n} ({b_correct/n:.3f})")
    print(f"F1:        A = {f1_score(cases, a_pred):.3f}   "
          f"B = {f1_score(cases, b_pred):.3f}")
    print(f"\nMcNemar discordant pairs: b(A ok, B wrong)={b_cnt}  "
          f"c(A wrong, B ok)={c_cnt}")
    print(f"McNemar exact two-sided p = {p_exact:.4f}")

    # Paired bootstrap CI of accuracy difference (A - B)
    rng = random.Random(SEED)
    diffs = []
    for _ in range(BOOTSTRAP_N):
        sample = [common[rng.randrange(n)] for _ in range(n)]
        d = (sum(1 for cid in sample if a_pred[cid] == cases[cid][0])
             - sum(1 for cid in sample if b_pred[cid] == cases[cid][0])) / n
        diffs.append(d)
    diffs.sort()
    lo = diffs[int(0.025 * BOOTSTRAP_N)]
    hi = diffs[int(0.975 * BOOTSTRAP_N)]
    acc_diff = (a_correct - b_correct) / n
    print(f"\nAccuracy difference (A - B) = {acc_diff:+.3f}, "
          f"bootstrap 95% CI [{lo:+.3f}, {hi:+.3f}] "
          f"(n={BOOTSTRAP_N}, seed={SEED})")
    print("Conclusion: " + (
        "no significant difference at alpha=0.05" if p_exact >= 0.05
        else f"significant difference at alpha=0.05 (p={p_exact:.4f})"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
