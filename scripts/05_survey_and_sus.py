#!/usr/bin/env python3
"""
05_survey_and_sus.py -- Addresses R1-C7 (survey denominators / 42.9%), R2-M7 (usability stats), R2-minor (42.9%).

Part A  survey_table(): prints k/n, % and Wilson 95% CI for every claim -> paste into a new table.
Part B  sus(): reads a CSV with columns p_id,q1..q10 (+ optional task_time_s, task_success, errors)
        and prints mean, SD, 95% t-CI, adjective band and objective-measure summaries.

USAGE   python 05_survey_and_sus.py            (Part A with the claims below; edit CLAIMS)
        python 05_survey_and_sus.py sus_raw.csv
"""
import sys
import numpy as np
import pandas as pd
from scipy import stats

# EDIT: (label, k, n) -- take k and n from the Microsoft Forms export, NOT from rounded percentages.
CLAIMS = [
    ("Industry: would trust AI-assisted validation (E3)", 3, 7),
    ("Industry: early validation reduces rework (E1)", 7, 7),
    ("Students: visuals help learning (E2-Acad)", 15, 17),
    ("All: manual review is a bottleneck", 33, 41),
    ("All: AI detection improves productivity", 34, 41),
    ("All: diagrams communicate better than text", 37, 41),
]


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def survey_table():
    rows = []
    for lab, k, n in CLAIMS:
        lo, hi = wilson(k, n)
        rows.append(dict(item=lab, k=k, n=n, pct=round(100 * k / n, 1),
                         ci95=f"[{100*lo:.0f}, {100*hi:.0f}]"))
    print("SURVEY DENOMINATORS (k of n) WITH WILSON 95% CI")
    print(pd.DataFrame(rows).to_string(index=False))


def sus_score(r):                      # r: 10 responses 1..5, Brooke (1996)
    odd = sum(r[i] - 1 for i in (0, 2, 4, 6, 8))
    even = sum(5 - r[i] for i in (1, 3, 5, 7, 9))
    return 2.5 * (odd + even)


def sus(path):
    df = pd.read_csv(path)
    q = [f"q{i}" for i in range(1, 11)]
    s = df[q].apply(lambda r: sus_score(r.tolist()), axis=1)
    n = len(s)
    m, sd = s.mean(), s.std(ddof=1)
    h = stats.t.ppf(.975, n - 1) * sd / np.sqrt(n)
    print(f"n={n}  mean={m:.1f}  SD={sd:.2f}  95% CI [{m-h:.1f}, {m+h:.1f}]  min={s.min():.1f} max={s.max():.1f}")
    # Bangor et al. (2009) adjective scale (approximate bands); Sauro-Lewis curved grades differ slightly.
    adj = ("Best imaginable" if m >= 90 else "Excellent" if m >= 80.3 else "Good" if m >= 71.4 else
           "OK" if m >= 50.9 else "Poor")
    print("Adjective (Bangor et al.):", adj)
    print("Participants >= 68 (industry benchmark):", int((s >= 68).sum()), "/", n)
    if "task_success" in df:
        print("Task completion rate: %.0f%%" % (100 * df.task_success.mean()))
    if "task_time_s" in df:
        print("Task time (s): mean %.0f, SD %.0f" % (df.task_time_s.mean(), df.task_time_s.std(ddof=1)))
    if "errors" in df:
        print("Errors per participant: mean %.2f" % df.errors.mean())
    # Item-level means help to say WHICH aspects are weak
    print(df[q].mean().round(2).to_string())


if __name__ == "__main__":
    sus(sys.argv[1]) if len(sys.argv) > 1 else survey_table()
