#!/usr/bin/env python3
"""
08_final_report.py -- final tables / figures / paper numbers from the frozen
evaluation run files.

USAGE (repo root):
  backend/venv/bin/python scripts/08_final_report.py \
      --runs backend/evaluation_results_groq-gpt-oss-120b_run1.json \
             backend/evaluation_results_groq-gpt-oss-120b_run3.json \
      --out paper_assets_final --frozen-threshold 0.90

Only runs whose status == "COMPLETE" are used; the others are listed and
skipped, so an INCOMPLETE run can never contribute a number to the paper.

Inputs are the files written by scripts/run_frozen_eval.py. Both layouts are
accepted:
  d["detailed_results_by_path"][path] = [records]   (preferred, per-path)
  d["detailed_results"] = [{path: {...}}, ...]       (headline = hybrid)

Outputs (in --out):
  paper_numbers.md                       every reported number, auto-generated
  table_overall_<path>_<thr>.csv         TP/FP/FN/TN + P/R/F1 + bootstrap 95% CI
  table_per_class_<path>.csv             per-category P/R/F1 (Wilson CI on recall)
  table_sweep_<path>.csv                 P/R/F1 across confidence thresholds
  fig_heatmap_<path>.png                 category confusion matrix
  fig_sweep_<path>.png                   threshold sweep
  disagreements_by_path.csv              per-case verdicts per path
"""
import argparse
import collections
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import binomtest

CLS = ["ambiguity", "incomplete", "inconsistency", "unverifiable"]
NORM = {"incompleteness": "incomplete", "unverifiability": "unverifiable"}
PATHS = ["rules", "llm", "hybrid"]
RNG = np.random.default_rng(42)
BOOTSTRAP_B = 5000

# Confidence threshold at which the reported (headline) defect count is taken.
# 0.90 is the dev-selected frozen threshold (FREEZE.md); 0.70 is the BR-10
# production filter, reported alongside for transparency.
THRESHOLDS = {"frozen": 0.90, "BR10_0.70": 0.70}


def norm(k):
    return NORM.get((k or "").lower(), (k or "").lower())


def records(d, path):
    """id -> record for one analysis path, for either supported file layout."""
    by_path = d.get("detailed_results_by_path")
    if by_path and path in by_path:
        return {r["id"]: r for r in by_path[path]}
    out = {}
    for r in d.get("detailed_results", []):
        if path in r:
            out[r["id"]] = dict(r[path], id=r["id"], expert=r["expert"],
                                expert_defect_type=r.get("expert_defect_type"))
    return out


def defects(r):
    """[(type, confidence)] for one record.

    Prefers the per-defect list; falls back to the per-record confidence and
    the type counts when only those are stored.
    """
    raw = r.get("defects_raw") or []
    out = [(norm(x.get("type") or x.get("defect_type")), float(x.get("confidence", 0)))
           for x in raw if isinstance(x, dict)]
    if out:
        return out
    if r.get("vis_prediction") == "DEFECT":
        c = float(r.get("confidence", 0))
        counts = r.get("defect_type_counts") or {}
        pairs = [(norm(k), c) for k, v in counts.items() for _ in range(int(v))]
        return pairs or [("ambiguity", c)]
    return []


def build(d, path, th):
    """Per-case gold/prediction frame for one path at one threshold."""
    rows = []
    for cid, r in sorted(records(d, path).items()):
        ds = [(t, c) for t, c in defects(r) if c >= th]
        cnt = collections.Counter(t for t, _ in ds)
        gold = r["expert"] == "DEFECT"
        rows.append(dict(id=cid, gold=gold,
                         gold_type=norm(r.get("expert_defect_type")) if gold else "none",
                         pred=bool(ds),
                         pred_type=(max(cnt, key=cnt.get) if cnt else "none")))
    return pd.DataFrame(rows).set_index("id")


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def counts(df):
    return (int((df.pred & df.gold).sum()), int((df.pred & ~df.gold).sum()),
            int((~df.pred & df.gold).sum()), int((~df.pred & ~df.gold).sum()))


def boot(df, B=BOOTSTRAP_B):
    """Percentile bootstrap 95% CI for P, R and F1."""
    v = []
    for _ in range(B):
        s = df.iloc[RNG.integers(0, len(df), len(df))]
        tp, fp, fn, _ = counts(s)
        v.append(prf(tp, fp, fn))
    a = np.array(v)
    return [tuple(np.percentile(a[:, i], [2.5, 97.5])) for i in range(3)]


def wilson(k, n, z=1.96):
    """Wilson score interval for a proportion (per-category recall)."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    # Clamp: the bound is mathematically in [0, 1]; floating point can push it
    # a hair outside (e.g. -0.0 for k = 0).
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar_exact(b, c):
    """Two-sided exact McNemar (binomial) p-value on discordant pairs."""
    if b + c == 0:
        return 1.0
    return float(binomtest(b, b + c, 0.5).pvalue)


def harness_kind(d):
    """'one-call' if the LLM and HYBRID paths share a single provider call,
    'two-call' if they came from two independent calls, 'unknown' if the
    result file does not record enough to tell.

    The frozen protocol requires ONE provider call per case, so a two-call run
    is not comparable with a one-call run and must not be pooled with it.
    """
    llm = records(d, "llm")
    hybrid = records(d, "hybrid")
    if not llm or not hybrid:
        return "unknown"
    same_defects = same_time = compared = 0
    for cid, lr in llm.items():
        hr = hybrid.get(cid)
        if hr is None:
            continue
        compared += 1
        if [x.get("type") for x in (lr.get("defects_raw") or [])] == \
           [x.get("type") for x in (hr.get("defects_raw") or [])]:
            same_defects += 1
        el, eh = lr.get("elapsed_ms"), hr.get("elapsed_ms")
        if el is not None and eh is not None and abs(el - eh) <= 1:
            same_time += 1
    if compared == 0:
        return "unknown"
    if same_defects == compared and same_time == compared:
        return "one-call"
    # Two independent calls never share a latency, and they can differ in
    # their defect sets; a shared call always shares both.
    if same_time < compared:
        return "two-call"
    return "unknown"


def main(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    md = ["# paper_numbers.md (auto-generated)", "",
          f"Frozen evaluation runs (reported confidence threshold "
          f"{a.frozen_threshold}).", ""]

    runs, skipped = [], []
    for f in a.runs:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        (runs if d.get("status") == "COMPLETE" else skipped).append((f, d))

    # ---- harness compatibility guard -------------------------------------
    # The frozen protocol requires ONE provider call per case. Runs produced
    # by the earlier two-call harness are not comparable with one-call runs
    # and must never be pooled with them.
    kinds = {}
    for f, d in runs:
        kinds.setdefault(harness_kind(d), []).append(Path(f).name)
    incompatible = sorted(set(kinds) - {"one-call"})
    for k in sorted(kinds):
        md_k = f" - `{', '.join(kinds[k])}`"
        if k == "one-call":
            md_k += " (one provider call per case)"
        elif k == "two-call":
            md_k += " (TWO provider calls per case - not comparable with one-call runs)"
        else:
            md_k += " (could not be classified)"
        md.append(f"- harness: {k}{md_k}")
    if incompatible and "one-call" in kinds:
        md += ["", "**WARNING: runs with different harness kinds were given "
                   "together. Only the one-call runs are valid under the frozen "
                   "protocol; the others are excluded below.**"]
        runs = [(f, d) for f, d in runs if harness_kind(d) == "one-call"]
    elif incompatible:
        md += ["", "**No one-call run available: the supplied COMPLETE runs were "
                   "produced by the earlier two-call harness and are not valid "
                   "under the frozen protocol. No metrics are reported.**"]
        (out / "paper_numbers.md").write_text("\n".join(md), encoding="utf-8")
        print("\n".join(md))
        raise SystemExit("No one-call COMPLETE run.")

    md += ["", "## Runs used", "",
           f"Complete runs used: {len(runs)} | skipped (not COMPLETE): {len(skipped)}", ""]
    for f, d in runs:
        p = d.get("provenance", {})
        md.append(f"- **USED** `{Path(f).name}` - run {p.get('run')}, "
                  f"{p.get('timestamp_utc')}, LLM answered "
                  f"{p.get('llm_answered')}, inter-case delay "
                  f"{p.get('inter_case_delay_s')}s")
    for f, d in skipped:
        p = d.get("provenance", {})
        md.append(f"- **SKIPPED (not COMPLETE)** `{Path(f).name}` - status "
                  f"`{d.get('status')}`, LLM answered {p.get('llm_answered')}, "
                  f"failures {p.get('failure_classification')}. Not reported as a result.")

    if not runs:
        md += ["", "**No COMPLETE run available - no metrics can be reported.**"]
        (out / "paper_numbers.md").write_text("\n".join(md), encoding="utf-8")
        print("\n".join(md))
        raise SystemExit("No COMPLETE run.")

    # ---- Table VI: frozen configuration (from the first reported run) ----
    prov = runs[0][1].get("provenance", {})
    first_run_label = f"run {prov.get('run')}"
    md += ["", f"## Table VI - frozen configuration (provenance of {first_run_label})", "",
           "| Item | Value |", "|---|---|"]
    for k in ("profile", "model_configured", "endpoint_host", "temperature",
              "max_tokens", "reasoning_effort", "prompt_file", "prompt_sha256",
              "hybrid_mode", "split_seed", "dataset", "dataset_size",
              "inter_case_delay_s", "git_commit", "git_tag", "timestamp_utc"):
        if k in prov:
            md.append(f"| {k} | `{prov[k]}` |")
    md.append(f"| confidence threshold (reported) | {a.frozen_threshold} |")
    md.append(f"| model actually returned | "
              f"{', '.join(prov.get('model_returned_unique') or [])} |")

    # ---- Per-path metrics ----
    for path in PATHS:
        md += ["", f"## Path: {path}"]
        for tname, th in THRESHOLDS.items():
            per_run = [build(d, path, th) for _, d in runs]
            m = np.array([prf(*counts(df)[:3]) for df in per_run])
            first = per_run[0]
            tp, fp, fn, tn = counts(first)
            P, R, F = prf(tp, fp, fn)
            ci = boot(first)
            md += ["", f"### {path} @ threshold {tname} ({th})", "",
                   f"- {first_run_label}: TP/FP/FN/TN = {tp}/{fp}/{fn}/{tn} (n={len(first)})",
                   f"- Precision = {P:.3f} [95% CI {ci[0][0]:.3f}, {ci[0][1]:.3f}]",
                   f"- Recall = {R:.3f} [95% CI {ci[1][0]:.3f}, {ci[1][1]:.3f}]",
                   f"- F1 = {F:.3f} [95% CI {ci[2][0]:.3f}, {ci[2][1]:.3f}]"]
            if len(per_run) > 1:
                sd = lambda col: m[:, col].std(ddof=1)
                md += [f"- across {len(per_run)} complete runs: "
                       f"P = {m[:, 0].mean():.3f} +/- {sd(0):.3f}, "
                       f"R = {m[:, 1].mean():.3f} +/- {sd(1):.3f}, "
                       f"F1 = {m[:, 2].mean():.3f} +/- {sd(2):.3f}"]
                same = np.mean([
                    len({(bool(df.loc[i].pred), df.loc[i].pred_type)
                         for df in per_run}) == 1
                    for i in first.index])
                md.append(f"- per-case output stability (identical verdict AND type "
                          f"in all {len(per_run)} runs) = {same:.3f}")
            else:
                md.append("- single complete run: no stability estimate available")
            pd.DataFrame([dict(path=path, threshold=th, TP=tp, FP=fp, FN=fn, TN=tn,
                               precision=P, p_lo=ci[0][0], p_hi=ci[0][1],
                               recall=R, r_lo=ci[1][0], r_hi=ci[1][1],
                               f1=F, f_lo=ci[2][0], f_hi=ci[2][1])]).to_csv(
                out / f"table_overall_{path}_{tname}.csv", index=False)

        # ---- per-category table + heat-map (frozen threshold, first run) ----
        df = build(runs[0][1], path, a.frozen_threshold)
        rows = []
        for c in CLS:
            tp = int(((df.gold_type == c) & (df.pred_type == c)).sum())
            fp = int(((df.gold_type != c) & (df.pred_type == c)).sum())
            fn = int(((df.gold_type == c) & (df.pred_type != c)).sum())
            n = int((df.gold_type == c).sum())
            p, r, f = prf(tp, fp, fn)
            lo, hi = wilson(tp, n)
            rows.append(dict(category=c, n=n, TP=tp, FP=fp, FN=fn,
                             precision=p, recall=r, recall_lo=lo, recall_hi=hi, f1=f))
        pc = pd.DataFrame(rows)
        pc.to_csv(out / f"table_per_class_{path}.csv", index=False)
        md += ["", f"### {path}: per-category metrics "
                   f"(threshold {a.frozen_threshold}, {first_run_label})", "",
               pc.round(3).to_markdown(index=False), "",
               f"Macro-F1 over the 4 categories = {pc.f1.mean():.3f}"]

        cols = CLS + ["none"]
        cm = np.zeros((4, 5), int)
        for _, r in df[df.gold].iterrows():
            if r.gold_type in CLS:
                cm[CLS.index(r.gold_type),
                   cols.index(r.pred_type) if r.pred_type in cols else 4] += 1
        fig, ax = plt.subplots(figsize=(8, 5.5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["Ambiguity", "Incomplete", "Inconsistency",
                                 "Unverifiable", "Not detected"],
                    yticklabels=[f"{c.capitalize()} (n={cm[i].sum()})"
                                 for i, c in enumerate(CLS)])
        ax.set_title(f"Category confusion - {path} - gpt-oss-120b "
                     f"(threshold {a.frozen_threshold})")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Expert")
        ax.tick_params(axis="x", rotation=20)
        for lbl in ax.get_xticklabels():
            lbl.set_ha("right")
        fig.tight_layout()
        fig.savefig(out / f"fig_heatmap_{path}.png", dpi=300)
        plt.close(fig)

        # ---- threshold sweep ----
        sw = []
        for th in [0, .5, .6, .7, .75, .8, .85, .9, .95]:
            tp, fp, fn, _ = counts(build(runs[0][1], path, th))
            p, r, f = prf(tp, fp, fn)
            sw.append(dict(threshold=th, precision=p, recall=r, f1=f))
        sw = pd.DataFrame(sw)
        sw.to_csv(out / f"table_sweep_{path}.csv", index=False)
        fig, ax = plt.subplots(figsize=(6, 4))
        for k in ["precision", "recall", "f1"]:
            ax.plot(sw.threshold, sw[k], marker="o", label=k)
        ax.axvline(.7, ls="--", c="grey")
        ax.axvline(a.frozen_threshold, ls=":", c="k")
        ax.set_xlabel("Confidence threshold")
        ax.set_ylabel("Score")
        ax.legend()
        ax.set_title(f"Threshold sweep - {path}")
        fig.tight_layout()
        fig.savefig(out / f"fig_sweep_{path}.png", dpi=300)
        plt.close(fig)

    # ---- category-level detail: detection vs. correct labelling ----------
    md += ["", "## Category-level detection vs. correct labelling "
               f"({first_run_label}, threshold {a.frozen_threshold}, LLM path)", "",
           "Binary recall counts a case as found when *any* defect is reported. "
           "This table separates 'flagged as a defect' from 'flagged with the "
           "correct category'.", ""]
    cls_rows = []
    for f, d in runs:
        for r in records(d, "llm").values():
            ds = [x for x in defects(r) if x[1] >= a.frozen_threshold]
            gold = r["expert"] == "DEFECT"
            gtype = norm(r.get("expert_defect_type")) if gold else "none"
            cls_rows.append((d["provenance"].get("run"), r["id"], gold, gtype, ds))
    for run_no in sorted({c[0] for c in cls_rows}):
        rr = [c for c in cls_rows if c[0] == run_no]
        nonamb = [c for c in rr if c[2] and c[3] != "ambiguity"]
        flagged = sum(1 for c in nonamb if c[4])
        correct = sum(1 for c in nonamb
                      if any(t == c[3] for t, _ in c[4]))
        missed = [c[1] for c in nonamb if not c[4]]
        fp_types = collections.Counter()
        for c in rr:
            if not c[2] and c[4]:
                cnt = collections.Counter(t for t, _ in c[4])
                fp_types[max(cnt, key=cnt.get)] += 1
        md += [f"- run {run_no}: non-ambiguity defective cases = {len(nonamb)}, "
               f"flagged as a defect = {flagged}, "
               f"flagged with the CORRECT category = {correct}, "
               f"missed entirely = {len(missed)}"
               + (f" ({', '.join(missed)})" if missed else ""),
               f"  - false positives by predicted type: "
               f"{dict(fp_types) or 'none'}"]

    # ---- latency (per provider call, from the recorded elapsed_ms) ----
    md += ["", "## Latency", "",
           "Per-case provider latency recorded by the driver (`elapsed_ms`). "
           "In the one-call harness the LLM-only and HYBRID paths share one "
           "call, so the two paths report the same latency by construction.", ""]
    lat_rows = []
    for path in PATHS:
        vals = []
        for f, d in runs:
            vals += [r.get("elapsed_ms") for r in records(d, path).values()
                     if r.get("elapsed_ms") is not None]
        if not vals:
            continue
        a_ms = np.array(vals, dtype=float)
        lat_rows.append(dict(path=path, n_calls=len(a_ms),
                             mean_ms=round(a_ms.mean(), 1),
                             median_ms=round(float(np.median(a_ms)), 1),
                             p95_ms=round(float(np.percentile(a_ms, 95)), 1),
                             min_ms=round(a_ms.min(), 1),
                             max_ms=round(a_ms.max(), 1)))
    if lat_rows:
        ldf = pd.DataFrame(lat_rows)
        ldf.to_csv(out / "table_latency.csv", index=False)
        md += [ldf.to_markdown(index=False), ""]

    # ---- paired comparisons between paths (first run, frozen threshold) ----
    md += ["", f"## Paired comparison ({first_run_label}, threshold "
               f"{a.frozen_threshold}) - McNemar exact test on correct/incorrect verdict"]
    dfs = {p: build(runs[0][1], p, a.frozen_threshold) for p in PATHS}
    dis = pd.DataFrame(index=dfs["rules"].index)
    dis["gold"] = dfs["rules"].gold
    for p in PATHS:
        dis[p] = dfs[p].pred
    dis.to_csv(out / "disagreements_by_path.csv")
    for x, y in [("rules", "llm"), ("rules", "hybrid"), ("llm", "hybrid")]:
        cx = dfs[x].pred == dfs[x].gold
        cy = dfs[y].pred == dfs[y].gold
        b = int((cx & ~cy).sum())
        c = int((~cx & cy).sum())
        pval = mcnemar_exact(b, c)
        md.append(f"- {x} vs {y}: only {x} correct = {b}, only {y} correct = {c}, "
                  f"McNemar exact p = {pval:.3f}")

    (out / "paper_numbers.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print("\n... full file:", out / "paper_numbers.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", default="paper_assets_final")
    ap.add_argument("--frozen-threshold", type=float, default=0.90)
    main(ap.parse_args())
