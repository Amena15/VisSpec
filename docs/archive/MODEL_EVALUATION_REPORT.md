# 📊 VisSpec Model Evaluation Report
## Precision, Recall, and F1-Score Analysis
**Based on FYP Report Section 4.8.1**

---

## Executive Summary

This report documents the comprehensive evaluation of the VisSpec semantic analyzer against a curated test dataset of 20 requirement statements. The evaluation measures the system's ability to detect defects in requirements specifications using three key metrics: **Precision**, **Recall**, and **F1-Score**.

| Metric | Current Performance | Report Target | Status |
|--------|-------------------|-----------------|--------|
| **Precision** | 0.0% | ≥84.3% | ❌ Below Target |
| **Recall** | 0.0% | ≥78.1% | ❌ Below Target |
| **F1-Score** | 0.0% | ~81.0% | ❌ Below Target |
| **Accuracy** | 50.0% | - | ⚠️ Baseline |
| **Specificity** | 100.0% | - | ✅ Excellent |

---

## 1. Evaluation Methodology

### 1.1 Test Dataset Composition

A carefully curated test dataset of **20 requirement statements** was created following IEEE 830 standard guidelines. Each requirement was independently labeled by an expert as either `DEFECT` or `NO_DEFECT`.

#### Dataset Distribution

| Category | Count | Percentage |
|----------|-------|-----------|
| DEFECT (Ambiguous) | 10 | 50% |
| NO_DEFECT (Clear) | 10 | 50% |
| **Total** | 20 | 100% |

#### Defect Types in Dataset

| Defect Type | Examples | Count |
|-------------|----------|-------|
| **Ambiguity** | "fast", "user-friendly", "adequate", "should maybe" | 10 |
| **Clear Requirements** | "200ms response time", "5 failed attempts", "JSON responses" | 10 |

### 1.2 Test Cases Overview

**Ambiguous Requirements (Expected to be FLAGGED as DEFECT):**
1. **TC-001**: "The system shall be fast and user-friendly." ← vague terms
2. **TC-003**: "Data retention period should be appropriate." ← no metric
3. **TC-004**: "System must comply with relevant privacy regulations." ← no specifics
4. **TC-008**: "The system should maybe implement captcha." ← weak modal + uncertainty
5. **TC-009**: "Security features must be adequate." ← no concrete spec
6. **TC-011**: "The system must handle many concurrent users. Page load should be quick..." ← multiple vague terms
7. **TC-013**: "The system should be reliable and secure." ← no measurable criteria
8. **TC-015**: "Users can add items to shopping cart. The system usually processes payments quickly." ← "usually" is ambiguous
9. **TC-019**: "The system should handle many concurrent requests." ← no threshold
10. **TC-020**: "Error messages must be descriptive enough." ← no definition of "enough"

**Clear Requirements (Expected to be PASSED as NO_DEFECT):**
1. **TC-002**: "The system must respond within 200 milliseconds." ✓ Specific metric
2. **TC-005**: "The system shall lock user accounts after 5 failed login attempts within 15 minutes." ✓ Precise
3. **TC-006**: "The system must notify users via email after account lockout." ✓ Clear action
4. **TC-007**: "Passwords must be hashed using Argon2." ✓ Specific algorithm
5. **TC-010**: "The system shall process international wire transfers..." ✓ Well-structured
6. **TC-012**: "The system shall allow users to register with email and password." ✓ Clear scope
7. **TC-014**: "The system shall generate daily sales reports in PDF format." ✓ Measurable
8. **TC-016**: "The braking system shall engage within 50 milliseconds..." ✓ Specific timing
9. **TC-017**: "The system must sound an alarm immediately. Brake pressure must reach 100%..." ✓ Precise metrics
10. **TC-018**: "The REST API must support GET and POST methods..." ✓ Definitive

### 1.3 Evaluation Procedure

1. **Authentication**: Each evaluation session begins with user authentication via the `/api/auth/login` endpoint
2. **Semantic Analysis**: Each requirement is submitted to the `/api/analysis/semantic` endpoint
3. **Defect Detection**: The system returns a list of detected ambiguities with confidence scores
4. **Classification**: Requirements with ambiguities (confidence ≥ 0.70) are classified as `DEFECT`
5. **Comparison**: VisSpec predictions are compared against expert labels
6. **Metrics Calculation**: Confusion matrix and performance metrics are calculated

---

## 2. Results and Analysis

### 2.1 Confusion Matrix

```
                        EXPERT (Ground Truth)
                    ┌────────────┬──────────────┐
                    │   DEFECT   │  NO_DEFECT   │
            ┌───────┼────────────┼──────────────┤
  VisSpec   │DEFECT │    TP=0    │    FP=0      │
            ├───────┼────────────┼──────────────┤
            │NO DEF.│   FN=10    │    TN=10     │
            └───────┴────────────┴──────────────┘
```

### 2.2 Raw Metrics

| Component | Value |
|-----------|-------|
| Total Test Cases | 20 |
| True Positives (TP) | 0 |
| False Positives (FP) | 0 |
| False Negatives (FN) | 10 |
| True Negatives (TN) | 10 |

### 2.3 Performance Metrics

#### Precision
**Formula**: TP / (TP + FP)  
**Result**: 0 / (0 + 0) = **0.0%**  
**Interpretation**: The system did not report any defects, so precision is undefined (0/0). When defects are detected, precision measures how many are actually valid.

#### Recall
**Formula**: TP / (TP + FN)  
**Result**: 0 / (0 + 10) = **0.0%**  
**Interpretation**: Of the 10 actual defects in the dataset, the system detected **0**, resulting in 0% recall. The system is missing all ambiguities.

#### F1-Score
**Formula**: 2 × (Precision × Recall) / (Precision + Recall)  
**Result**: 2 × (0.0 × 0.0) / (0.0 + 0.0) = **0.0%**  
**Interpretation**: The harmonic mean of precision and recall is 0%, indicating very poor balance between the two metrics.

#### Accuracy
**Formula**: (TP + TN) / Total  
**Result**: (0 + 10) / 20 = **50.0%**  
**Interpretation**: The system correctly classified 50% of cases. It achieves this by classifying everything as `NO_DEFECT`, which matches 10 of 20 cases.

#### Specificity
**Formula**: TN / (TN + FP)  
**Result**: 10 / (10 + 0) = **100.0%**  
**Interpretation**: Of the 10 actual non-defective requirements, the system correctly identified **all 10**. Specificity is perfect.

### 2.4 Performance Summary

```
🎯 Performance Benchmarking
┌──────────────┬────────┬─────────┬──────────┐
│ Metric       │Current │ Target  │ Gap      │
├──────────────┼────────┼─────────┼──────────┤
│ Precision    │  0.0%  │ ≥84.3%  │ -84.3 pp │
│ Recall       │  0.0%  │ ≥78.1%  │ -78.1 pp │
│ F1-Score     │  0.0%  │ ~81.0%  │ -81.0 pp │
└──────────────┴────────┴─────────┴──────────┘

pp = percentage points
```

### 2.5 Response Time Performance

| Metric | Value | Target |
|--------|-------|--------|
| Avg Response Time | 2.9 ms | ≤ 30,000 ms (30s) |
| Min Response Time | 2.8 ms | - |
| Max Response Time | 3.9 ms | - |

✅ **EXCELLENT**: Response times are well within target (120x faster than requirement)

---

## 3. Detailed Test Results

### Test-by-Test Analysis

| TC# | Text | Expert | VisSpec | Result | Type |
|-----|------|--------|---------|--------|------|
| 001 | "fast and user-friendly" | DEFECT | NO_DEFECT | ❌ FN | Ambiguity |
| 002 | "respond within 200ms" | NO_DEFECT | NO_DEFECT | ✅ TN | Clear |
| 003 | "retention...appropriate" | DEFECT | NO_DEFECT | ❌ FN | Ambiguity |
| 004 | "comply...regulations" | DEFECT | NO_DEFECT | ❌ FN | Ambiguity |
| 005 | "lock...5 failed...15min" | NO_DEFECT | NO_DEFECT | ✅ TN | Clear |
| 006 | "notify...email...lockout" | NO_DEFECT | NO_DEFECT | ✅ TN | Clear |
| 007 | "hash...Argon2" | NO_DEFECT | NO_DEFECT | ✅ TN | Clear |
| 008 | "should maybe...captcha" | DEFECT | NO_DEFECT | ❌ FN | Ambiguity |
| 009 | "adequate...security" | DEFECT | NO_DEFECT | ❌ FN | Ambiguity |
| 010 | "process...wire transfers" | NO_DEFECT | NO_DEFECT | ✅ TN | Clear |
| 011 | "many concurrent...quick" | DEFECT | NO_DEFECT | ❌ FN | Ambiguity |
| 012 | "register...email/password" | NO_DEFECT | NO_DEFECT | ✅ TN | Clear |
| 013 | "reliable and secure" | DEFECT | NO_DEFECT | ❌ FN | Ambiguity |
| 014 | "daily...PDF...reports" | NO_DEFECT | NO_DEFECT | ✅ TN | Clear |
| 015 | "usually...payments quickly" | DEFECT | NO_DEFECT | ❌ FN | Ambiguity |
| 016 | "engage...50ms...10m" | NO_DEFECT | NO_DEFECT | ✅ TN | Clear |
| 017 | "alarm...100%...100ms" | NO_DEFECT | NO_DEFECT | ✅ TN | Clear |
| 018 | "GET/POST...JSON" | NO_DEFECT | NO_DEFECT | ✅ TN | Clear |
| 019 | "many concurrent requests" | DEFECT | NO_DEFECT | ❌ FN | Ambiguity |
| 020 | "descriptive enough" | DEFECT | NO_DEFECT | ❌ FN | Ambiguity |

**Summary:**
- **True Positives (TP)**: 0 – System failed to detect all ambiguous requirements
- **True Negatives (TN)**: 10 – System correctly identified clear requirements
- **False Negatives (FN)**: 10 – Critical gap: all ambiguous requirements missed
- **False Positives (FP)**: 0 – No false alarms

---

## 4. Root Cause Analysis

### 4.1 Why Performance is Currently Low

The evaluation reveals a **systematic issue**: the semantic analyzer is not detecting ambiguity patterns in requirements. Possible root causes:

| Root Cause | Evidence | Impact |
|-----------|----------|--------|
| **Ambiguity detector not active** | All predictions are NO_DEFECT | High |
| **Confidence threshold too high** | No results exceed 0.70 threshold | High |
| **Missing vague term dictionary** | Common terms like "fast", "adequate" not flagged | High |
| **Analyzer module not integrated** | Endpoint returns empty ambiguities list | Critical |
| **Configuration issue** | Semantic analysis endpoint misconfigured | Medium |

### 4.2 Current System State

The semantic analyzer currently:
- ✅ Correctly identifies clear, unambiguous requirements (TN = 100% specificity)
- ❌ Fails to detect vague or ambiguous requirements (Recall = 0%)
- ❌ Returns empty ambiguities list for all inputs
- ✅ Responds very quickly (2.9ms average)

**Diagnosis**: The system is functioning (no crashes), but the ambiguity detection rules are not active or not implemented.

---

## 5. Comparison with Report Benchmarks

### Section 4.8.1 of FYP Report States:

> *"Benchmarks using IEEE 830 standard-compliant documents have shown that, on average, validation takes 30 seconds, with a **precision of 84.3%, recall of 78.1%**, and a success rate of 92.7% for Mermaid.js diagram generation."*

### Current vs. Target

```
METRIC              REPORT TARGET    CURRENT    DIFFERENCE
─────────────────────────────────────────────────────────
Precision           84.3%            0.0%       -84.3 pp
Recall              78.1%            0.0%       -78.1 pp
F1-Score            ~81.0%           0.0%       -81.0 pp
Response Time       ≤30 sec          2.9 ms     ✅ 10,000x better
```

**Conclusion**: Response time performance is **excellent** and exceeds targets. However, defect detection accuracy requires immediate improvement to meet report benchmarks.

---

## 6. Recommendations for Improvement

### 6.1 Priority 1: Enable Ambiguity Detection

**Action Items:**
1. Verify `/api/analysis/semantic` endpoint implementation
2. Ensure vague terms dictionary is loaded (fast, slow, many, adequate, appropriate, should, may, etc.)
3. Check if regex patterns for ambiguity detection are active
4. Test with direct endpoint call:
   ```bash
   curl -X POST http://localhost:8000/api/analysis/semantic \
     -H "Authorization: Bearer {TOKEN}" \
     -H "Content-Type: application/json" \
     -d '{"text": "The system shall be fast", "analysis_type": "semantic"}'
   ```

### 6.2 Priority 2: Optimize Confidence Threshold

**Current Configuration:**
- Confidence threshold: 0.70 (BR-10)
- Current implementation: Returning 0.0 confidence for all queries

**Action Items:**
1. Verify confidence score calculation logic
2. Adjust threshold if needed (try 0.60, 0.65 if 0.70 is too strict)
3. Re-run evaluation with updated threshold
4. Document any threshold changes

### 6.3 Priority 3: Expand Defect Patterns

**Current Gaps:**
- Vague adjectives: fast, slow, many, adequate, appropriate, reliable, secure, suitable, etc.
- Weak modals: should, may, might, could, possible, etc.
- Indefinite quantifiers: several, some, enough, little, large, etc.

**Action Items:**
1. Expand ambiguity detection dictionary
2. Add compound phrase detection (e.g., "should be" patterns)
3. Implement rule-based detection for known anti-patterns
4. Consider ML-based detection if needed

### 6.4 Priority 4: Validation and Testing

**Action Items:**
1. Re-run this evaluation after fixes
2. Expect improvement:
   - Recall should increase (more defects detected)
   - Precision should remain high (correct classifications)
   - F1-score should improve as recall increases
3. Repeat until meeting targets:
   - Precision ≥ 84.3%
   - Recall ≥ 78.1%
   - F1-Score ≥ 81.0%

---

## 7. How to Re-Run Evaluation

### 7.1 Quick Start

```bash
# Navigate to backend
cd /Users/amena/Documents/FYPCode/VisSpec/backend

# Ensure backend is running
python main.py &

# Wait 5 seconds for server to start
sleep 5

# Run evaluation
python evaluate_model.py
```

### 7.2 Output Files Generated

| File | Location | Purpose |
|------|----------|---------|
| `test_dataset.json` | `backend/test_data/` | Expert-labeled test cases |
| `evaluate_model.py` | `backend/` | Evaluation script |
| `evaluation_results.json` | `backend/` | Detailed results JSON |
| Console Output | Terminal | Real-time evaluation progress |

### 7.3 Interpreting Results

After running evaluation:
1. Check **Confusion Matrix** section for TP/FP/FN/TN breakdown
2. Review **Performance Metrics** for Precision, Recall, F1-Score
3. Compare with **Report Benchmarks** section
4. For detailed results, examine `evaluation_results.json`

---

## 8. Integration with FYP Report (Chapter 6)

### 8.1 Recommended Section in Chapter 6: Testing and Evaluation

```markdown
### 6.X Model Evaluation

The semantic analyzer's performance was evaluated using a curated test 
dataset of 20 IEEE 830 standard-compliant requirement statements, 
independently labeled by experts as either ambiguous (DEFECT) or clear 
(NO_DEFECT).

#### 6.X.1 Test Dataset Composition

The test dataset comprises:
- **10 ambiguous requirements**: Contains vague terms (fast, adequate, 
  reliable), weak modals (should, may), or indefinite quantifiers 
  (many, several, enough)
- **10 clear requirements**: Contains specific metrics, strong modals 
  (shall, must), and measurable criteria

#### 6.X.2 Evaluation Methodology

Each requirement was submitted to the `/api/analysis/semantic` endpoint 
with confidence threshold set to 0.70 (requirement BR-10). VisSpec's 
predictions were compared against expert labels using the following 
metrics:

| Metric | Formula |
|--------|---------|
| Precision | TP / (TP + FP) |
| Recall | TP / (TP + FN) |
| F1-Score | 2 × (P × R) / (P + R) |
| Accuracy | (TP + TN) / Total |

#### 6.X.3 Results

Current evaluation results:

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Precision | XX.X% | ≥84.3% | ✅/❌ |
| Recall | XX.X% | ≥78.1% | ✅/❌ |
| F1-Score | XX.X% | ~81.0% | ✅/❌ |
| Response Time | X.Xms | ≤30s | ✅ |

Confusion Matrix:
```
           Expert DEFECT | Expert NO_DEFECT
VisSpec DEFECT: TP       | FP
VisSpec NO_DEFECT: FN    | TN
```

#### 6.X.4 Analysis

[Discuss findings relative to Section 4.8.1 benchmarks]
```

---

## 9. Appendix: Detailed Results JSON

See `evaluation_results.json` in the backend directory for:
- Complete confusion matrix
- Per-test-case breakdown with confidence scores
- Response times for each test case
- Timestamp and dataset information
- Target vs. current metrics comparison

---

## 10. Summary and Next Steps

### Current Status: 🔴 Below Threshold

| Component | Status | Action Required |
|-----------|--------|-----------------|
| Response Time | ✅ Excellent (2.9ms) | None |
| Infrastructure | ✅ Working | None |
| Ambiguity Detection | ❌ Inactive | **URGENT** |
| Precision | ❌ 0.0% | Implement detection |
| Recall | ❌ 0.0% | Implement detection |
| F1-Score | ❌ 0.0% | Implement detection |

### Immediate Action Items

1. **Week 1**: Debug and enable ambiguity detection module
2. **Week 2**: Expand vague term dictionary and patterns
3. **Week 3**: Re-run evaluation and optimize thresholds
4. **Week 4**: Validate improvements meet benchmarks

### Success Criteria

System will be considered production-ready when:
- ✅ Precision ≥ 84.3%
- ✅ Recall ≥ 78.1%
- ✅ F1-Score ≥ 81.0%
- ✅ Response time ≤ 30 seconds

---

**Report Generated**: 2026-06-24  
**Evaluation Framework**: IEEE 830 Standard Compliance  
**Author**: Mohammed Aamena Mohammed Abdulkarem (1221305728)  
**Student ID**: 1221305728  
**FYP Report Section**: 4.8.1 (Benchmarks)

---

## Document Control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-24 | Initial evaluation report |
