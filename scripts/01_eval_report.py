#!/usr/bin/env python3
"""
01_eval_report.py  --  Addresses R1-C1/C2/C5, R2-M2/M3/M6 and the "42.9%" / confidence-score minor comments.

Run from the repo root:
    python scripts/01_eval_report.py \
        --dataset backend/test_data/held_out_test_set.json \
        --results backend/evaluation_results.json \
        --out     paper_assets

Produces (in --out):
    table_benchmark_distribution.csv   -> new Table (benchmark composition)
    table_per_class_metrics.csv        -> new Table (per-category P/R/F1 + 95% CI)
    table_overall_metrics.csv          -> replaces/extends Table I (with 95% bootstrap CIs)
    table_threshold_sweep.csv          -> justification of the 0.70 confidence threshold
    fig_confusion_heatmap.png          -> replaces Fig. 7 (adds "Not detected" column)
    fig_threshold_sweep.png            -> new figure (P/R/F1 vs. threshold)
    fig_confidence_hist.png            -> shows the confidence-score distribution
"""
import argparse, json, collections
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

CLASSES = ["ambiguity", "incomplete", "inconsistency", "unverifiable"]
NORM = {"incompleteness": "incomplete", "unverifiability": "unverifiable"}
RNG = np.random.default_rng(42)


def norm(k):
    k = (k or "").strip().lower()
    return NORM.get(k, k)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def load(dataset, results):
    ds = {c["id"]: c for c in json.load(open(dataset))}
    rs = json.load(open(results))["detailed_results"]
    rows = []
    for x in rs:
        counts = collections.Counter()
        for k, v in (x.get("defect_type_counts") or {}).items():
            counts[norm(k)] += int(v)
        top = max(counts, key=counts.get) if counts else None
        rows.append(dict(
            id=x["id"],
            gold_defect=(x["expert"] == "DEFECT"),
            gold_type=norm(ds[x["id"]].get("defect_type")) if x["expert"] == "DEFECT" else "none",
            pred_defect=(x["vis_prediction"] == "DEFECT"),
            pred_type=top if top else "none",
            conf=float(x["confidence"]),
        ))
    return pd.DataFrame(rows)


def binary_metrics(df, th=0.0):
    pred = df.pred_defect & (df.conf >= th)
    tp = int((pred & df.gold_defect).sum()); fp = int((pred & ~df.gold_defect).sum())
    fn = int((~pred & df.gold_defect).sum()); tn = int((~pred & ~df.gold_defect).sum())
    return tp, fp, fn, tn


def bootstrap_ci(df, th=0.0, B=5000):
    n = len(df); vals = []
    for _ in range(B):
        s = df.iloc[RNG.integers(0, n, n)]
        tp, fp, fn, _ = binary_metrics(s, th); vals.append(prf(tp, fp, fn))
    a = np.array(vals)
    return {m: (np.percentile(a[:, i], 2.5), np.percentile(a[:, i], 97.5)) for i, m in enumerate("PRF")}



def main(a):
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    df = load(a.dataset, a.results)

    # ---- 1. Benchmark composition (R1-C1, R2-M3)
    comp = df.gold_type.value_counts().rename_axis("category").reset_index(name="n")
    comp["share_%"] = (100 * comp.n / len(df)).round(1)
    comp.to_csv(out / "table_benchmark_distribution.csv", index=False)
    print("\nBENCHMARK COMPOSITION (N=%d)\n" % len(df), comp.to_string(index=False))

    # ---- 2. Overall binary metrics, with and without BR-10 threshold, + bootstrap CI
    rows = []
    for label, th in [("as evaluated (no threshold applied)", 0.0), ("BR-10 enforced (conf >= 0.70)", 0.70)]:
        tp, fp, fn, tn = binary_metrics(df, th); p, r, f = prf(tp, fp, fn)
        ci = bootstrap_ci(df, th)
        rows.append(dict(setting=label, TP=tp, FP=fp, FN=fn, TN=tn,
                         precision=round(p, 4), p_lo=round(ci["P"][0], 4), p_hi=round(ci["P"][1], 4),
                         recall=round(r, 4), r_lo=round(ci["R"][0], 4), r_hi=round(ci["R"][1], 4),
                         f1=round(f, 4), f_lo=round(ci["F"][0], 4), f_hi=round(ci["F"][1], 4),
                         accuracy=round((tp + tn) / len(df), 4)))
    ov = pd.DataFrame(rows); ov.to_csv(out / "table_overall_metrics.csv", index=False)
    print("\nOVERALL (binary: defect vs. no defect)\n", ov.to_string(index=False))

    # ---- 3. Per-category one-vs-rest P/R/F1 + Wilson CI on recall  (R1-C2, R2-M2)
    rows = []
    for c in CLASSES:
        tp = int(((df.gold_type == c) & (df.pred_type == c)).sum())
        fp = int(((df.gold_type != c) & (df.pred_type == c)).sum())
        fn = int(((df.gold_type == c) & (df.pred_type != c)).sum())
        support = int((df.gold_type == c).sum())
        p, r, f = prf(tp, fp, fn); lo, hi = wilson(tp, support)
        rows.append(dict(category=c, support=support, TP=tp, FP=fp, FN=fn,
                         precision=round(p, 3), recall=round(r, 3),
                         recall_CI95=f"[{lo:.2f}, {hi:.2f}]", f1=round(f, 3)))
    pc = pd.DataFrame(rows)
    macro_all = pc.f1.mean()
    macro_supported = pc[pc.support >= 5].f1.mean()
    pc.to_csv(out / "table_per_class_metrics.csv", index=False)
    print("\nPER-CATEGORY (type-level, one-vs-rest)\n", pc.to_string(index=False))
    print(f"\nMacro-F1 over 4 categories = {macro_all:.3f};  over categories with >=5 cases = {macro_supported:.3f}")

    # ---- 4. Threshold sweep (R1-C5, R2-M6)
    rows = []
    for th in [0.0, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9]:
        tp, fp, fn, tn = binary_metrics(df, th); p, r, f = prf(tp, fp, fn)
        rows.append(dict(threshold=th, precision=p, recall=r, f1=f, TP=tp, FP=fp, FN=fn))
    sw = pd.DataFrame(rows); sw.round(4).to_csv(out / "table_threshold_sweep.csv", index=False)
    print("\nTHRESHOLD SWEEP\n", sw.round(3).to_string(index=False))
    fig, ax = plt.subplots(figsize=(6, 4))
    for m in ["precision", "recall", "f1"]:
        ax.plot(sw.threshold, sw[m], marker="o", label=m.capitalize())
    ax.axvline(0.70, ls="--", c="grey")
    ax.set_xlabel("Confidence threshold"); ax.set_ylabel("Score")
    ax.set_title("Effect of confidence threshold on detection metrics")
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(out / "fig_threshold_sweep.png", dpi=300); plt.close(fig)

    # ---- 5. Confusion heat-map WITH a 'Not detected' column  (replaces Fig. 7)
    cols = CLASSES + ["none"]
    cm = np.zeros((4, 5), int)
    for _, r in df[df.gold_defect].iterrows():
        if r.gold_type in CLASSES:
            j = cols.index(r.pred_type) if r.pred_type in cols else 4
            cm[CLASSES.index(r.gold_type), j] += 1
    pct = cm / np.maximum(cm.sum(1, keepdims=True), 1) * 100
    annot = np.array([[f"{cm[i,j]}\n({pct[i,j]:.0f}%)" if cm[i, j] else "0" for j in range(5)] for i in range(4)])
    pretty = ["Ambiguity", "Incomplete", "Inconsistency", "Unverifiable"]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    sns.heatmap(cm, annot=annot, fmt="", cmap="Blues", linewidths=1, linecolor="white",
                xticklabels=pretty + ["Not detected"],
                yticklabels=[f"{p} (n={cm[i].sum()})" for i, p in enumerate(pretty)],
                cbar_kws={"label": "Number of cases"}, ax=ax)
    ax.set_xlabel("Predicted category (most frequent type returned)"); ax.set_ylabel("Expert label")
    ax.set_title("Defect-category confusion matrix (defective cases only)")
    fig.tight_layout(); fig.savefig(out / "fig_confusion_heatmap.png", dpi=300); plt.close(fig)

    # ---- 6. Confidence-score distribution: shows scores are discrete, i.e. NOT calibrated probabilities
    fig, ax = plt.subplots(figsize=(6, 4))
    d = df[df.pred_defect]
    if len(d):
        ax.hist([d[d.gold_defect].conf, d[~d.gold_defect].conf],
                bins=np.arange(0.5, 1.01, 0.05),
                label=["true defect (TP)", "no defect (FP)"], stacked=True)
        ax.axvline(0.70, ls="--", c="grey")
    ax.set_xlabel("Reported confidence"); ax.set_ylabel("Cases")
    ax.set_title("Confidence scores of flagged requirements"); ax.legend(); fig.tight_layout()
    fig.savefig(out / "fig_confidence_hist.png", dpi=300); plt.close(fig)
    print("\nDistinct confidence values emitted:", sorted(df[df.pred_defect].conf.unique()))
    print(f"\nFiles written to {out.resolve()}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="backend/test_data/held_out_test_set.json")
    ap.add_argument("--results", default="backend/evaluation_results.json")
    ap.add_argument("--out", default="paper_assets")
    main(ap.parse_args())
