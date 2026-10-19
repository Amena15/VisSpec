#!/usr/bin/env python3
"""
04_rq3_traceability_experiment.py -- Addresses R1-C3 and R2-Major-1 (controlled with/without traceability comparison).

Design (within-subjects, paired): the SAME requirement set -> diagram elements under two conditions
   A = baseline : LLM output used as-is
   B = VisSpec  : LLM output + traceability enforcement (every actor/message must be grounded in a cited requirement)
Definition: an element (actor or message) is HALLUCINATED if its content is not supported by the source requirement(s)
   it is attributed to (judged by >=2 independent raters, blind to condition).

Steps
   python scripts/04_rq3_traceability_experiment.py grounding-demo          # sanity test of the enforcement filter (runs offline)
   python scripts/04_rq3_traceability_experiment.py sheet  elements.json    # -> blinded rating sheet (CSV) for 2 raters
   python scripts/04_rq3_traceability_experiment.py analyze ratings.csv     # -> hallucination rates, paired test, kappa, CI
elements.json = [{"case":"S01","condition":"A","req_text":{"R1":"..."},"actors":["User",...],
                  "messages":[{"from":"User","to":"System","text":"login","req_id":"R1"}]}, ...]
(produce it by running your generator with enforcement OFF (A) and ON (B) on >=30 requirement sets)
"""
import sys, re, json, random, csv
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

# Single source of truth for grounding predicates: the SAME module the
# production diagram generator uses (backend/services/diagram/
# traceability_enforcement.py), so the experiment evaluates the mechanism the
# application actually ships.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.services.diagram.traceability_enforcement import (  # noqa: E402
    toks, stem, grounded_actor, grounded_message as _grounded_msg,
)


def grounded_message(msg, sources, min_overlap=0.5):
    """Wrapper matching this script's message-dict API."""
    return _grounded_msg(msg["text"], msg.get("req_id"), sources, min_overlap)


def enforce(case):
    """Condition B: drop untraceable elements. Returns filtered copy + rejection counts."""
    src = case["req_text"]
    actors = [x for x in case["actors"] if grounded_actor(x, src)]
    msgs = [m for m in case["messages"] if grounded_message(m, src)
            and m["from"] in actors and m["to"] in actors]
    return dict(case, actors=actors, messages=msgs,
                rejected=(len(case["actors"]) - len(actors), len(case["messages"]) - len(msgs)))


def demo():
    case = dict(case="demo", condition="A",
                req_text={"R1": "The customer shall upload a document to the system.",
                          "R2": "The system shall store the document in the database."},
                actors=["Customer", "System", "Database", "Auditor"],
                messages=[dict(**{"from": "Customer", "to": "System", "text": "upload document", "req_id": "R1"}),
                          dict(**{"from": "System", "to": "Database", "text": "store document", "req_id": "R2"}),
                          dict(**{"from": "System", "to": "Auditor", "text": "send audit email", "req_id": "R2"})])
    out = enforce(case)
    print("kept actors:", out["actors"], "| kept messages:", len(out["messages"]),
          "| rejected (actors, msgs):", out["rejected"])


def sheet(path):
    items = json.load(open(path)); rows = []
    for c in items:
        for kind, els in (("actor", c["actors"]), ("message", c["messages"])):
            for e in els:
                text = e if kind == "actor" else f'{e["from"]} -> {e["to"]}: {e["text"]}'
                rows.append(dict(case=c["case"], condition=c["condition"], kind=kind, element=text,
                                 source=" | ".join(f"{k}: {v}" for k, v in c["req_text"].items()),
                                 rater1="", rater2=""))
    random.Random(7).shuffle(rows)                  # shuffle -> raters blind to condition
    pd.DataFrame(rows).to_csv("rating_sheet_FULL.csv", index=False)
    pd.DataFrame(rows).drop(columns=["condition"]).to_csv("rating_sheet_for_raters.csv", index=False)
    print(len(rows), "elements -> rating_sheet_for_raters.csv (give to raters), rating_sheet_FULL.csv (keep)")
    print("Rater instruction: write 1 if the element is SUPPORTED by the source text, 0 if NOT supported (hallucinated).")


def analyze(path):
    df = pd.read_csv(path); df = df.dropna(subset=["rater1", "rater2"])
    po = (df.rater1 == df.rater2).mean(); p1 = df.rater1.mean(); p2 = df.rater2.mean()
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    print(f"Raw agreement {po:.3f}  Cohen kappa {(po - pe) / (1 - pe):.3f}")
    df["hall"] = ((df.rater1 + df.rater2) < 2).astype(int)   # conservative: hallucinated if EITHER rater says unsupported
    g = df.groupby(["case", "condition"]).hall.mean().unstack()
    print("Mean hallucination rate per diagram:\n", g.mean().round(3).to_string())
    d = (g["A"] - g["B"]).dropna()
    w = stats.wilcoxon(d) if (d != 0).any() else None
    print(f"Paired reduction A-B: mean {d.mean():.3f}  Wilcoxon p={w.pvalue if w else 'n/a'}  n={len(d)} diagrams")
    rng = np.random.default_rng(0)
    bs = [d.sample(len(d), replace=True, random_state=int(rng.integers(1e9))).mean() for _ in range(5000)]
    print("95% bootstrap CI of reduction:", np.round(np.percentile(bs, [2.5, 97.5]), 3))
    sup = df[df.condition == "A"]
    print("Element-level hallucination in A:", round(sup.hall.mean(), 3),
          "| in B:", round(df[df.condition == "B"].hall.mean(), 3))
    print("Report ALSO the cost: supported elements removed by the filter (recall loss) = supported_A - supported_B")


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"grounding-demo": demo, "sheet": lambda: sheet(sys.argv[2]), "analyze": lambda: analyze(sys.argv[2])}[cmd]()
