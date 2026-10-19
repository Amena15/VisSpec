#!/usr/bin/env python3
"""
02_interrater_kappa.py -- Addresses R1-C1 and R2-M3 (inter-rater agreement, disagreement resolution).

INPUT  (CSV, one row per requirement):  id,text,rater1,rater2,rater3
       labels: ambiguity | incomplete | inconsistency | unverifiable | none
       (use the ORIGINAL independent labels, before any discussion/adjudication)
USAGE  python scripts/02_interrater_kappa.py annotations.csv
OUTPUT pairwise Cohen's kappa, Fleiss' kappa, % raw agreement, a disagreement list for adjudication,
       and gold_labels.csv (majority vote; ties flagged for adjudication).
"""
import sys, itertools, collections
import numpy as np, pandas as pd


def cohen(a, b):
    labs = sorted(set(a) | set(b)); n = len(a)
    po = np.mean([x == y for x, y in zip(a, b)])
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labs)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def fleiss(M):                       # M: items x categories (counts), constant raters per item
    N, k = M.shape; n = M.sum(1)[0]
    P_i = (np.square(M).sum(1) - n) / (n * (n - 1)); P = P_i.mean()
    p_j = M.sum(0) / (N * n); Pe = np.square(p_j).sum()
    return (P - Pe) / (1 - Pe) if Pe < 1 else 1.0


def band(k):  # Landis & Koch (1977)
    return ("poor" if k < 0 else "slight" if k <= .20 else "fair" if k <= .40 else
            "moderate" if k <= .60 else "substantial" if k <= .80 else "almost perfect")


def main(path):
    df = pd.read_csv(path); rc = [c for c in df.columns if c.startswith("rater")]
    print(f"{len(df)} items, {len(rc)} raters")
    for a, b in itertools.combinations(rc, 2):
        k = cohen(df[a].tolist(), df[b].tolist())
        print(f"Cohen kappa {a} vs {b}: {k:.3f} ({band(k)})")
    cats = sorted(set(df[rc].values.ravel()))
    M = np.array([[row[rc].tolist().count(c) for c in cats] for _, row in df.iterrows()])
    kf = fleiss(M); print(f"Fleiss kappa (all raters): {kf:.3f} ({band(kf)})")
    # defect / no-defect agreement (binary view)
    bdf = df.copy(); bdf[rc] = (bdf[rc] != "none").astype(int).astype(str)
    Mb = np.array([[row[rc].tolist().count(c) for c in ["0", "1"]] for _, row in bdf.iterrows()])
    print(f"Fleiss kappa (defect vs. no-defect): {fleiss(Mb):.3f}")
    print(f"Items with unanimous agreement: {(M.max(1) == len(rc)).sum()}/{len(df)}")
    gold = []
    for _, row in df.iterrows():
        cnt = collections.Counter(row[rc]); top, n = cnt.most_common(1)[0]
        tie = list(cnt.values()).count(n) > 1
        gold.append(("ADJUDICATE" if tie else top, n < len(rc)))
    df["gold"] = [g for g, _ in gold]; df["disagreement"] = [d for _, d in gold]
    df[df.disagreement].to_csv("disagreements_for_adjudication.csv", index=False)
    df.to_csv("gold_labels.csv", index=False)
    print("Wrote gold_labels.csv and disagreements_for_adjudication.csv")


if __name__ == "__main__":
    main(sys.argv[1])
