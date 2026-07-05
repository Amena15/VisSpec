#!/usr/bin/env python3
"""Multi-Class Confusion Matrix Heatmap for Defect Types (4x4)

Rows: Actual defect type (expert_defect_type) for cases where expert == "DEFECT"
Columns: Predicted defect type, defined as the most frequent key in defect_type_counts

Outputs: multi_class_heatmap.png

Expected input files:
- backend/test_data/test_dataset.json
- backend/evaluation_results.json

Notes:
- Uses the 4 defect types used in the evaluation dataset:
  ambiguity, incomplete, inconsistency, unverifiable
- If a DEFECT case has no defect_type_counts (or the predicted type is not in the 4 types),
  it is skipped to keep a strict 4x4 matrix.
"""

import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_predicted_defect_key(key: str) -> str:
    """Normalize predicted defect keys to match our 4-class heatmap labels."""
    k = (key or "").strip().lower()

    # Observed spelling mismatch in evaluation_results.json
    mapping = {
        "incompleteness": "incomplete",
    }
    return mapping.get(k, k)


def primary_predicted_type(defect_type_counts: dict) -> str | None:
    if not defect_type_counts:
        return None

    normalized_counts = defaultdict(int)
    for raw_key, count in defect_type_counts.items():
        norm_key = normalize_predicted_defect_key(raw_key)
        if count is None:
            continue
        normalized_counts[norm_key] += int(count)

    if not normalized_counts:
        return None

    return max(normalized_counts.keys(), key=lambda k: normalized_counts.get(k, 0))


def main():
    repo_root = Path(__file__).resolve().parents[1]  # backend/
    dataset_path = repo_root / "test_data" / "test_dataset.json"
    results_path = repo_root / "evaluation_results.json"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Missing test dataset: {dataset_path}")
    if not results_path.exists():
        raise FileNotFoundError(f"Missing evaluation results: {results_path}")

    test_cases = load_json(dataset_path)
    results = load_json(results_path)

    # id -> expert defect type
    expert_map = {case["id"]: case.get("defect_type") for case in test_cases}

    # 4x4 labels (match screenshot)
    defect_types = ["ambiguity", "incomplete", "inconsistency", "unverifiable"]
    type_to_idx = {t: i for i, t in enumerate(defect_types)}

    pretty_labels = {
        "ambiguity": "Ambiguity",
        "incomplete": "Incomplete",
        "inconsistency": "Inconsistency",
        "unverifiable": "Unverifiable",
    }

    cm = np.zeros((4, 4), dtype=int)

    expert_counts = defaultdict(int)
    skipped = 0

    for item in results.get("detailed_results", []):
        case_id = item.get("id")
        expert_verdict = item.get("expert")

        # Only build rows for expert DEFECT cases
        if expert_verdict != "DEFECT":
            continue

        actual = item.get("expert_defect_type") or expert_map.get(case_id)
        if actual not in type_to_idx:
            continue

        expert_counts[actual] += 1

        predicted = primary_predicted_type(item.get("defect_type_counts", {}))
        if predicted not in type_to_idx:
            skipped += 1
            continue

        cm[type_to_idx[actual], type_to_idx[predicted]] += 1

    # ======================
    # Console (screenshot-like)
    # ======================
    print("\nVISSPEC - MULTI-CLASS CONFUSION MATRIX")

    header = f"{'Actual \\ Predicted':<18}" + " ".join(
        [f"{pretty_labels[t]:<12}" for t in defect_types]
    )
    print(header)

    for i, t in enumerate(defect_types):
        row_vals = " ".join([f"{cm[i, j]:<12d}" for j in range(4)])
        print(f"{pretty_labels[t]:<18} {row_vals}")

    print("\nExpert type counts:")
    for t in defect_types:
        print(f"  {pretty_labels[t]}: {expert_counts[t]}")
    if skipped:
        print(f"\n⚠️ Skipped {skipped} DEFECT cases due to missing/unknown prediction type.")

    # ======================
    # Heatmap: Counts + Row Percentages (diagonal highlighted)
    # ======================
    fig, ax = plt.subplots(figsize=(9, 7))

    # Calculate row percentages (normalize per actual class)
    row_sums = cm.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    cm_percent = (cm / row_sums) * 100

    # Annotate as: Count (Percentage%)
    annot_text = np.empty_like(cm, dtype="U24")
    for i in range(4):
        for j in range(4):
            if cm[i, j] > 0:
                annot_text[i, j] = f"{cm[i, j]} ({cm_percent[i, j]:.1f}%)"
            else:
                annot_text[i, j] = "0"

    sns.heatmap(
        cm,
        annot=annot_text,
        fmt="",
        cmap="Blues",
        xticklabels=[pretty_labels[t] for t in defect_types],
        yticklabels=[pretty_labels[t] for t in defect_types],
        ax=ax,
        linewidths=1,
        linecolor="white",
        annot_kws={"size": 10, "fontweight": "bold"},
        cbar_kws={"label": "Number of Test Cases"},
    )

    ax.set_xlabel("Predicted Defect Type", fontsize=14, fontweight="bold")

    ax.set_ylabel("Actual Defect Type (Expert)", fontsize=14, fontweight="bold")
    ax.set_title(
        "VisSpec - 4x4 Multi-Class Defect Type Confusion Matrix",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )

    plt.tight_layout()

    out_path = repo_root / "multi_class_heatmap.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()

    print(f"\n✅ Saved heatmap: {out_path}")


if __name__ == "__main__":
    main()

