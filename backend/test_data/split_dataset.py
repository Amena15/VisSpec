"""
One-off helper to split the master evaluation dataset (test_dataset.json)
into a development set and a held-out test set.

Rationale (methodology integrity):
- Rule-based thresholds/lexicons are tuned ONLY on dev_set.json.
- The rules are then FROZEN before running the final evaluation on
  held_out_test_set.json, so no test information leaks into tuning.

Run:  python -m backend.test_data.split_dataset
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "test_dataset.json"
DEV = HERE / "dev_set.json"
HELD = HERE / "held_out_test_set.json"


def main() -> None:
    with SRC.open() as f:
        data = json.load(f)

    # Stratify by (expert_verdict, defect_type) to preserve class balance.
    groups = defaultdict(list)
    for item in data:
        groups[(item["expert_verdict"], item.get("defect_type"))].append(item)

    random.seed(42)  # reproducible split
    dev, held = [], []
    for _key, items in sorted(groups.items(), key=lambda x: (str(x[0][0]), str(x[0][1]))):
        random.shuffle(items)
        # ~1/3 to held-out; guarantee at least one held-out sample when possible.
        n_held = max(1, round(len(items) * 0.34)) if len(items) >= 3 else (1 if len(items) >= 2 else 0)
        held.extend(items[:n_held])
        dev.extend(items[n_held:])

    dev.sort(key=lambda x: x["id"])
    held.sort(key=lambda x: x["id"])

    DEV.write_text(json.dumps(dev, indent=2, ensure_ascii=False))
    HELD.write_text(json.dumps(held, indent=2, ensure_ascii=False))

    def breakdown(rows):
        return dict(Counter((d["expert_verdict"], d.get("defect_type")) for d in rows))

    print("FULL :", len(data), breakdown(data))
    print("DEV  :", len(dev), breakdown(dev))
    print("HELD :", len(held), breakdown(held))


if __name__ == "__main__":
    main()
