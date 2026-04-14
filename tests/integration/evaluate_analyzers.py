#!/usr/bin/env python3
"""
Evaluate Semantic and Predictive Analyzer Performance.

Measures:
1. Semantic Analyzer: Precision, Recall, F1-Score for ambiguity detection
2. Predictive Analyzer: Complexity error (MAE), Risk accuracy
"""

import json
import sys
import os
from typing import Dict, List, Tuple

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from services.ai.semantic_analyzer import SemanticAnalyzer
from services.ai.predictive_analyzer import PredictiveAnalyzer


# ============================================================
# GROUND TRUTH LABELED DATASET
# ============================================================

SEMANTIC_TEST_DATA = [
    {
        "name": "Vague Security Requirement",
        "text": "The system should have good security. Passwords must be adequate. Users may access appropriate resources.",
        "actual_ambiguities": [
            "should", "good", "adequate", "may", "appropriate"
        ]
    },
    {
        "name": "Well-Written Requirement",
        "text": "The system shall lock accounts after 5 failed login attempts within 15 minutes.",
        "actual_ambiguities": []
    },
    {
        "name": "Healthcare with Vague Terms",
        "text": "The system should maintain patient data appropriately. Only authorized medical staff can access records. Data retention should be reasonable.",
        "actual_ambiguities": [
            "should", "appropriately", "should", "reasonable"
        ]
    },
    {
        "name": "E-Commerce Vague",
        "text": "The system usually processes payments quickly. Orders may be cancelled before shipping. Refunds are sometimes issued.",
        "actual_ambiguities": [
            "usually", "quickly", "may", "sometimes"
        ]
    },
    {
        "name": "Performance Vague",
        "text": "The web server must handle many concurrent requests. Page load time should be fast. Database queries must be optimized.",
        "actual_ambiguities": [
            "many", "should", "fast"
        ]
    },
    {
        "name": "Mixed Quality",
        "text": "REQ-001: The system shall allow password reset via email. REQ-002: Links must expire after a reasonable time. REQ-003: The system should log all attempts.",
        "actual_ambiguities": [
            "reasonable", "should"
        ]
    },
    {
        "name": "Banking Clear",
        "text": "The banking system must authenticate users using multi-factor authentication. Transactions exceeding $10,000 require supervisor approval within 2 business days.",
        "actual_ambiguities": []
    },
    {
        "name": "Vague Performance",
        "text": "The system should be fast and reliable. It may have a user-friendly interface. The software must handle many users. Security features must be adequate.",
        "actual_ambiguities": [
            "should", "fast", "reliable", "may", "user-friendly", "many", "adequate"
        ]
    },
]


PREDICTIVE_TEST_DATA = [
    {
        "name": "Simple Feature",
        "text": "The system shall display a welcome message to users after login.",
        "actual_complexity": 15,  # Simple UI feature
        "actual_risk": "low"
    },
    {
        "name": "CRUD Operations",
        "text": "Users can create, read, update, and delete their personal profile information. The system shall validate email format before saving. Profile changes must be logged with timestamps.",
        "actual_complexity": 30,  # Standard CRUD
        "actual_risk": "low"
    },
    {
        "name": "E-Commerce Checkout",
        "text": "The e-commerce system must calculate shipping costs based on user location, package weight, and selected shipping speed. The system shall apply discounts for orders over $50. Users can apply one promo code per order. Payment processing shall be handled by Stripe API.",
        "actual_complexity": 55,  # Multi-step with external API
        "actual_risk": "high"  # Payment processing = high risk
    },
    {
        "name": "Banking Transfer",
        "text": "The banking system shall process international wire transfers. The system must validate recipient bank details against SWIFT database. If validation fails, the system shall notify the user and log the attempt. For transfers exceeding $10,000, the system requires two-factor authentication and supervisor approval.",
        "actual_complexity": 65,  # Financial + validation + 2FA
        "actual_risk": "high"
    },
    {
        "name": "Healthcare Compliance",
        "text": "The healthcare system must maintain patient records with full audit trail. The system shall support role-based access (doctor, nurse, admin, patient). Patient data must be encrypted at rest and in transit. The system must comply with HIPAA and GDPR regulations. Data retention period is 7 years. Real-time synchronization required across 3 regional data centers.",
        "actual_complexity": 80,  # Compliance + encryption + sync
        "actual_risk": "very high"  # Patient data + HIPAA = very high
    },
    {
        "name": "Security Authentication",
        "text": "The authentication system must implement multi-factor authentication using SMS or authenticator app. Passwords must be hashed using Argon2. Accounts lock after 5 failed attempts for 15 minutes. JWT tokens expire after 60 minutes. Session timeout after 30 minutes of inactivity.",
        "actual_complexity": 50,  # Security implementation
        "actual_risk": "medium"
    },
    {
        "name": "Enterprise-Grade",
        "text": "The system must support multi-tenancy with complete data isolation between 500+ organizations. Real-time synchronization required across 5 regional data centers. 99.999% uptime required. Disaster recovery RPO = 15 minutes, RTO = 1 hour. Must support 1 million concurrent users. GDPR and CCPA compliance required.",
        "actual_complexity": 90,  # Enterprise architecture
        "actual_risk": "high"
    },
    {
        "name": "Real-Time Performance",
        "text": "The system must respond to user requests within 200 milliseconds at 95th percentile under 1000 concurrent users. Real-time notifications must be delivered within 5 seconds. The system must handle 10,000 transactions per second during peak hours. Database queries must complete within 50ms.",
        "actual_complexity": 70,  # Performance tuning
        "actual_risk": "high"  # Transactions = high risk keyword
    },
]


def evaluate_semantic_analyzer():
    """Evaluate semantic analyzer: Precision, Recall, F1-Score"""
    print("=" * 70)
    print("SEMANTIC ANALYZER PERFORMANCE EVALUATION")
    print("=" * 70)

    analyzer = SemanticAnalyzer()

    all_tp = 0  # True positives
    all_fp = 0  # False positives
    all_fn = 0  # False negatives

    for test in SEMANTIC_TEST_DATA:
        result = analyzer.analyze_text(test["text"])
        detected = result.get("ambiguities", [])

        # Extract detected ambiguity terms
        detected_terms = set()
        for amb in detected:
            term = amb.get("term", "").strip().lower()
            if term:
                detected_terms.add(term)

        # Actual ambiguity terms
        actual_terms = set(t.lower() for t in test["actual_ambiguities"])

        # Calculate TP, FP, FN
        tp = len(detected_terms & actual_terms)
        fp = len(detected_terms - actual_terms)
        fn = len(actual_terms - detected_terms)

        all_tp += tp
        all_fp += fp
        all_fn += fn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        status = "✅" if f1 >= 0.70 else "⚠️"
        print(f"\n{test['name']} {status}")
        print(f"  Actual:   {sorted(actual_terms)}")
        print(f"  Detected: {sorted(detected_terms)}")
        print(f"  Precision: {precision:.2f} | Recall: {recall:.2f} | F1: {f1:.2f}")

    # Overall metrics
    overall_precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) > 0 else 0.0
    overall_recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) > 0 else 0.0
    overall_f1 = (2 * overall_precision * overall_recall / (overall_precision + overall_recall)
                  if (overall_precision + overall_recall) > 0 else 0.0)

    print("\n" + "-" * 70)
    print("OVERALL SEMANTIC PERFORMANCE")
    print("-" * 70)
    print(f"  True Positives:  {all_tp}")
    print(f"  False Positives: {all_fp}")
    print(f"  False Negatives: {all_fn}")
    print(f"  Precision: {overall_precision:.2%} (target: ≥ 80%)")
    print(f"  Recall:    {overall_recall:.2%} (target: ≥ 75%)")
    print(f"  F1-Score:  {overall_f1:.2%} (target: ≥ 77%)")

    sem_pass = (overall_precision >= 0.80 and overall_recall >= 0.75 and overall_f1 >= 0.77)
    print(f"  Status: {'✅ PASS' if sem_pass else '⚠️ BELOW TARGET'}")

    return {
        "precision": round(overall_precision, 2),
        "recall": round(overall_recall, 2),
        "f1_score": round(overall_f1, 2),
        "tp": all_tp,
        "fp": all_fp,
        "fn": all_fn,
        "pass": sem_pass
    }


def evaluate_predictive_analyzer():
    """Evaluate predictive analyzer: Complexity MAE, Risk accuracy"""
    print("\n" + "=" * 70)
    print("PREDICTIVE ANALYZER ACCURACY EVALUATION")
    print("=" * 70)

    analyzer = PredictiveAnalyzer()

    complexity_errors = []
    risk_correct = 0
    risk_total = len(PREDICTIVE_TEST_DATA)

    for test in PREDICTIVE_TEST_DATA:
        result = analyzer.analyze_text(test["text"])
        predicted_complexity = result["complexity_score"]
        predicted_risk = result["risk_level"]

        actual_complexity = test["actual_complexity"]
        actual_risk = test["actual_risk"]

        # Complexity error
        error = abs(predicted_complexity - actual_complexity)
        complexity_errors.append(error)

        # Risk accuracy (normalize risk levels)
        risk_levels = {"low": 0, "medium": 1, "high": 2, "very high": 3}
        predicted_level = risk_levels.get(predicted_risk, 0)
        actual_level = risk_levels.get(actual_risk, 0)
        risk_match = (predicted_level == actual_level)
        if risk_match:
            risk_correct += 1

        status = "✅" if error <= 15 else "⚠️"
        print(f"\n{test['name']} {status}")
        print(f"  Predicted: {predicted_complexity} | Actual: {actual_complexity} | Error: {error}")
        print(f"  Risk Predicted: {predicted_risk} | Actual: {actual_risk} | {'✅' if risk_match else '❌'}")

    # Overall metrics
    mae = sum(complexity_errors) / len(complexity_errors) if complexity_errors else 0
    risk_accuracy = risk_correct / risk_total if risk_total > 0 else 0

    print("\n" + "-" * 70)
    print("OVERALL PREDICTIVE PERFORMANCE")
    print("-" * 70)
    print(f"  Mean Absolute Error (Complexity): {mae:.1f} points (target: ≤ 15)")
    print(f"  Max Error: {max(complexity_errors)}")
    print(f"  Min Error: {min(complexity_errors)}")
    print(f"  Risk Accuracy: {risk_accuracy:.2%} ({risk_correct}/{risk_total}) (target: ≥ 70%)")

    pred_pass = (mae <= 15 and risk_accuracy >= 0.70)
    print(f"  Status: {'✅ PASS' if pred_pass else '⚠️ BELOW TARGET'}")

    return {
        "mae": round(mae, 1),
        "max_error": max(complexity_errors),
        "min_error": min(complexity_errors),
        "risk_accuracy": round(risk_accuracy, 2),
        "risk_correct": risk_correct,
        "risk_total": risk_total,
        "pass": pred_pass
    }


def main():
    print("\n" + "█" * 70)
    print("█  VISPEC ANALYZER PERFORMANCE EVALUATION")
    print("█" * 70)

    semantic_results = evaluate_semantic_analyzer()
    predictive_results = evaluate_predictive_analyzer()

    # Final Summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print("\n📊 Semantic Analyzer:")
    print(f"   Precision: {semantic_results['precision']:.0%} {'✅' if semantic_results['precision'] >= 0.80 else '⚠️'} (target: ≥80%)")
    print(f"   Recall:    {semantic_results['recall']:.0%} {'✅' if semantic_results['recall'] >= 0.75 else '⚠️'} (target: ≥75%)")
    print(f"   F1-Score:  {semantic_results['f1_score']:.0%} {'✅' if semantic_results['f1_score'] >= 0.77 else '⚠️'} (target: ≥77%)")

    print("\n📈 Predictive Analyzer:")
    print(f"   MAE:          {predictive_results['mae']:.1f} pts {'✅' if predictive_results['mae'] <= 15 else '⚠️'} (target: ≤15)")
    print(f"   Risk Acc:     {predictive_results['risk_accuracy']:.0%} {'✅' if predictive_results['risk_accuracy'] >= 0.70 else '⚠️'} (target: ≥70%)")

    all_pass = semantic_results["pass"] and predictive_results["pass"]
    print(f"\n🏆 Overall: {'✅ ALL METRICS PASS' if all_pass else '⚠️ SOME METRICS BELOW TARGET'}")

    # Save results
    output = {
        "semantic": semantic_results,
        "predictive": predictive_results,
        "overall_pass": all_pass
    }

    output_path = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n💾 Results saved to: {output_path}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
