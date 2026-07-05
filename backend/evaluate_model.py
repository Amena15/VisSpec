"""
Model Evaluation Script - VisSpec FYP
Measures Precision, Recall, F1-Score (Section 4.8.1)
Author: Mohammed Aamena Mohammed Abdulkarem (1221305728)
Date: 2024
"""

import json
import sys
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.validation.validator import Validator

# Configuration
BASE_URL = "http://localhost:8000"

# Load test dataset
def load_test_data() -> List[Dict]:
    """Load test dataset from JSON file"""
    dataset_path = Path(__file__).parent / "test_data" / "test_dataset.json"
    if not dataset_path.exists():
        print(f"❌ Test dataset not found at {dataset_path}")
        sys.exit(1)
    
    with open(dataset_path, "r") as f:
        return json.load(f)

def predict_defect(text: str, validator: Validator) -> Tuple[bool, float, Dict[str, int]]:
    """Run VisSpec validation and determine if a defect exists.

    Returns:
      (has_defect, confidence_score, defect_type_counts)
    """
    try:
        result = validator.validate_text(text)
        defects = result.get("defects", [])
        defects_found = len(defects) > 0

        confidence = 0.0
        defect_type_counts: Dict[str, int] = {}
        if defects:
            confidence = max([d.get("confidence", 0.0) for d in defects])
            for d in defects:
                t = d.get("type", "unknown")
                defect_type_counts[t] = defect_type_counts.get(t, 0) + 1

        return defects_found, confidence, defect_type_counts
    except Exception:
        return False, 0.0, {}


def evaluate_model():
    """Main evaluation function"""

    print("\n" + "=" * 80)
    print("VISSPEC MODEL EVALUATION - PRECISION, RECALL, F1-SCORE")
    print("Based on FYP Report Section 4.8.1")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Load test data
    test_data = load_test_data()
    print(f"\n📊 Loaded {len(test_data)} test cases from test_dataset.json")

    validator = Validator(use_llm=False)
    print("\n🔐 Using local validator path (no external API dependency)")
    
    # Confusion matrix counters
    tp = 0  # True Positives: VisSpec says defect, Expert says defect
    fp = 0  # False Positives: VisSpec says defect, Expert says no defect
    fn = 0  # False Negatives: VisSpec says no defect, Expert says defect
    tn = 0  # True Negatives: VisSpec says no defect, Expert says no defect
    
    results = []
    total_time = 0
    
    print("\n🔍 Running predictions...")
    print("-" * 80)
    
    for i, item in enumerate(test_data, 1):
        text = item["text"]
        expert = item["expert_verdict"]
        defect_type = item.get("defect_type", "unknown")
        
        # Run VisSpec prediction
        start_time = time.time()
        vis_prediction, confidence, defect_type_counts = predict_defect(text, validator)

        elapsed = time.time() - start_time

        total_time += elapsed
        
        # Determine truth
        expert_defect = (expert == "DEFECT")
        
        # Update confusion matrix
        if vis_prediction and expert_defect:
            tp += 1
            verdict = "TP ✅"
            symbol = "✓"
        elif vis_prediction and not expert_defect:
            fp += 1
            verdict = "FP ❌"
            symbol = "✗"
        elif not vis_prediction and expert_defect:
            fn += 1
            verdict = "FN ❌"
            symbol = "✗"
        else:
            tn += 1
            verdict = "TN ✅"
            symbol = "✓"
        
        results.append({
            "id": item["id"],
            "text": text[:70] + ("..." if len(text) > 70 else ""),
            "expert": expert,
            "expert_defect_type": defect_type,
            "vis_prediction": "DEFECT" if vis_prediction else "NO_DEFECT",
            "confidence": round(confidence, 3),
            "verdict": verdict,
            "elapsed_ms": round(elapsed * 1000, 1),
            "defect_type_counts": defect_type_counts,
        })

        
        print(f"[{i:02d}] {symbol} {verdict:7} | Expert: {expert:8} | VisSpec: {'DEFECT' if vis_prediction else 'NO_DEFECT':8} | Conf: {confidence:.2f} | {text[:50]}...")
    
    avg_time = total_time / len(test_data) if test_data else 0
    
    # Calculate metrics
    total = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / total if total > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    print("\n" + "=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)
    
    print("\n📊 Confusion Matrix:")
    print(f"  ┌─────────────────────┬─────────────────────────────┐")
    print(f"  │                     │     EXPERT (Ground Truth)    │")
    print(f"  │                     ├──────────────┬──────────────┤")
    print(f"  │                     │   DEFECT     │  NO DEFECT   │")
    print(f"  ├─────────────────────┼──────────────┼──────────────┤")
    print(f"  │ VisSpec DEFECT      │  TP = {tp:2}  │  FP = {fp:2}   │")
    print(f"  ├─────────────────────┼──────────────┼──────────────┤")
    print(f"  │ VisSpec NO DEFECT   │  FN = {fn:2}  │  TN = {tn:2}   │")
    print(f"  └─────────────────────┴──────────────┴──────────────┘")
    
    print(f"\n📈 Classification Metrics:")
    print(f"  Total Samples:       {total}")
    print(f"  True Positives (TP): {tp}")
    print(f"  False Positives (FP):{fp}")
    print(f"  False Negatives (FN):{fn}")
    print(f"  True Negatives (TN): {tn}")
    
    print(f"\n🎯 Performance Metrics:")
    print(f"  │ Precision:   {precision:.2%}  (Target: ≥84.3%)")
    if precision >= 0.843:
        print(f"  │ Status:      ✅ PASS - Exceeds benchmark")
    else:
        gap = (0.843 - precision) * 100
        print(f"  │ Status:      ⚠️  NEEDS {gap:.1f}% improvement")
    
    print(f"\n  │ Recall:      {recall:.2%}  (Target: ≥78.1%)")
    if recall >= 0.781:
        print(f"  │ Status:      ✅ PASS - Exceeds benchmark")
    else:
        gap = (0.781 - recall) * 100
        print(f"  │ Status:      ⚠️  NEEDS {gap:.1f}% improvement")
    
    print(f"\n  │ F1-Score:    {f1:.2%}  (Target: ~81.0%)")
    if abs(f1 - 0.810) <= 0.05:
        print(f"  │ Status:      ✅ PASS - Within acceptable range")
    elif f1 >= 0.81:
        print(f"  │ Status:      ✅ PASS - Exceeds target")
    else:
        gap = (0.81 - f1) * 100
        print(f"  │ Status:      ⚠️  NEEDS {gap:.1f}% improvement")
    
    print(f"\n  │ Accuracy:    {accuracy:.2%}")
    print(f"  │ Specificity: {specificity:.2%}")
    print(f"  │ Avg Response:{avg_time*1000:.1f}ms (Target: ≤30s)")
    
    print("\n" + "=" * 80)
    print("COMPARISON WITH REPORT BENCHMARK (Section 4.8.1)")
    print("=" * 80)
    print(f"  Report Benchmark:")
    print(f"    Precision: 84.3% | Recall: 78.1% | F1-Score: ~81.0%")
    print(f"\n  VisSpec Results:")
    print(f"    Precision: {precision:.1%} | Recall: {recall:.1%} | F1-Score: {f1:.1%}")
    
    # Determine if targets met
    print(f"\n  Target Achievement:")
    precision_status = "✅ PASS" if precision >= 0.843 else "❌ NEEDS IMPROVEMENT"
    recall_status = "✅ PASS" if recall >= 0.781 else "❌ NEEDS IMPROVEMENT"
    f1_status = "✅ PASS" if f1 >= 0.81 else "❌ NEEDS IMPROVEMENT"
    
    print(f"    Precision (≥84.3%):  {precision:.1%} → {precision_status}")
    print(f"    Recall (≥78.1%):     {recall:.1%} → {recall_status}")
    print(f"    F1-Score (≥81.0%):   {f1:.1%} → {f1_status}")
    
    # Overall assessment
    passed = sum([1 for status in [precision_status, recall_status, f1_status] if "PASS" in status])
    print(f"\n  📊 Overall Score: {passed}/3 targets achieved")
    
    if passed == 3:
        print(f"  🎯 EXCELLENT: All targets met! System is production-ready.")
    elif passed >= 2:
        print(f"  ✅ GOOD: Most targets met. Minor improvements needed.")
    else:
        print(f"  ⚠️  FAIR: Significant improvements needed.")
    
    # Save detailed results
    results_file = Path(__file__).parent / "evaluation_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "dataset_size": len(test_data),
            "metrics": {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "accuracy": round(accuracy, 4),
                "specificity": round(specificity, 4),
                "avg_response_time_ms": round(avg_time * 1000, 1)
            },
            "confusion_matrix": {
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "true_negatives": tn
            },
            "benchmark": {
                "precision_target": 0.843,
                "recall_target": 0.781,
                "f1_target": 0.81
            },
            "status": {
                "precision_passed": precision >= 0.843,
                "recall_passed": recall >= 0.781,
                "f1_passed": f1 >= 0.81,
                "targets_met": passed
            },
            "detailed_results": results
        }, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    print("=" * 80)
    print()
    
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "targets_passed": passed
    }

if __name__ == "__main__":
    try:
        result = evaluate_model()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
