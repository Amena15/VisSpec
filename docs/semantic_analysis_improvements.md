# Semantic Analysis Endpoint Test Results & Improvement Recommendations

## Test Execution Summary

**Date:** April 14, 2026  
**Endpoint:** `POST http://localhost:8000/api/analysis/semantic`  
**Test Cases:** 10  
**Success Rate:** 10/10 (100%)  
**Method Used:** Heuristic fallback (LLaMA 3 not active)

---

## Test Results Overview

| # | Test Case | Confidence | Entities | Relations | Ambiguities | Assessment |
|---|-----------|------------|----------|-----------|-------------|------------|
| 1 | Well-Written Security Requirement | 0.70 | 8 | 4 | 2 | ✅ Good |
| 2 | Poorly-Written Requirement | 0.23 | 4 | 3 | 5 | ✅ Correctly identified as poor |
| 3 | Healthcare Domain | 0.55 | 8 | 2 | 2 | ⚠️ Moderate |
| 4 | Banking Domain | 0.70 | 9 | 4 | 1 | ✅ Good |
| 5 | E-Commerce Domain | 0.45 | 7 | 5 | 3 | ⚠️ Low-Moderate |
| 6 | Safety-Critical System | 0.70 | 7 | 5 | 1 | ✅ Good |
| 7 | API Requirements | 0.65 | 5 | 3 | 2 | ✅ Good |
| 8 | Mixed Quality | 0.65 | 7 | 3 | 2 | ✅ Good |
| 9 | Performance Requirements | 0.55 | 7 | 3 | 3 | ⚠️ Moderate |
| 10 | IEEE 830 Style SRS Fragment | 0.70 | 8 | 4 | 2 | ✅ Good |

---

## Key Findings

### ✅ Strengths

1. **Excellent Ambiguity Detection**
   - Correctly identifies vague terms: "appropriate", "relevant", "fast", "user-friendly"
   - Severity classification works well (high/medium/low)
   - Provides actionable suggestions

2. **Good Entity Extraction**
   - Successfully extracts: actors, systems, data entities, quality attributes, temporal requirements
   - Domain-specific detection works (healthcare, banking, safety-critical)

3. **Confidence Scoring is Meaningful**
   - Well-written requirements score 0.70 (at BR-10 threshold)
   - Poorly-written requirements score low (0.23)
   - Mixed quality falls in between (0.45-0.65)

4. **Relation Extraction**
   - Correctly identifies ACCESSS, COMPLIES_WITH, MAINTAINS relationships
   - Actor-to-entity relationships are accurate

### ⚠️ Areas for Improvement

#### 1. **Missing Method Field in Response**
**Issue:** All responses show `method: N/A`  
**Expected:** Should show "heuristic_fallback" or "llama3"  
**Root Cause:** The semantic analyzer returns dict with "method" key, but the API response schema doesn't include it

**Fix:**
```python
# In backend/api/analysis.py, add method field to SemanticAnalysisResponse
class SemanticAnalysisResponse(BaseModel):
    # ... existing fields
    method: str  # Add this
```

---

#### 2. **Entity Extraction Quality Issues**

**Issue 2a: Incorrect Entity Labels**
- "multi-factor authentication" labeled as QUALITY_ATTRIBUTE (should be CONSTRAINT or SYSTEM_COMPONENT)
- "GET, POST, PUT, and DELETE methods" as single entity (should be separate)
- "page load time" as QUALITY_ATTRIBUTE (should be TEMPORAL or METRIC)

**Improvement:**
```python
# Add better classification logic in semantic_analyzer.py
# Distinguish between:
# - Quality attributes (confidentiality, integrity, performance)
# - Metrics/Measurements (response time, load time, throughput)
# - Constraints/Technologies (MFA, Argon2, OAuth)
```

**Issue 2b: Negative Position Values**
- Some entities have `"start": -1, "end": -1` (implicit/inferred entities)
- This may cause issues in visualization or downstream processing

**Fix:**
```python
# Only add entities with valid positions OR mark them as "inferred"
if inferred:
    entity["inferred"] = True
    entity["start"] = 0  # or omit position fields
```

---

#### 3. **Ambiguity Detection Improvements**

**Issue 3a: False Positives on Modal Verbs**
- "shall" and "must" flagged as ambiguities (low severity)
- These are actually GOOD practice in requirements (IEEE 830 standard)
- Creates noise in well-written requirements

**Fix:**
```python
# Don't flag "shall" or "must" as ambiguities
# Only flag weak modals: "should", "may", "might", "could"
# Exception: flag "shall/must" ONLY if no consequence specified AND it's a safety-critical system
```

**Issue 3b: Missing Contextual Ambiguities**
- "5 failed login attempts" - doesn't flag what happens after lockout duration
- "within 50 milliseconds" - doesn't question measurement methodology
- "$10,000" - doesn't question currency or inflation adjustment

**Improvement:**
```python
# Add domain-specific ambiguity checks
def _check_domain_ambiguities(text: str, domain: str) -> List[Dict]:
    if domain == "safety_critical":
        # Check for missing safety margins, error bounds
        pass
    elif domain == "banking":
        # Check for missing audit requirements, compliance standards
        pass
```

---

#### 4. **Relation Extraction Enhancement**

**Issue 4a: Limited Relation Types**
Current: ACCESSES, COMPLIES_WITH, MAINTAINS, APPLIES_TO  
Missing:
- ENCRYPTS/PROTECTS (security operations)
- VALIDATES/VERIFIES (validation requirements)
- LOGS/RECORDS (audit requirements)
- NOTIFIES/ALERTS (notification requirements)

**Improvement:**
```python
# Add more relation patterns
notification_patterns = [
    (r'\b(notify|alert|inform|email|send)\b', "NOTIFIES"),
    (r'\b(log|record|audit|track)\b', "LOGS"),
    (r'\b(encrypt|hash|protect|secure)\b', "PROTECTS"),
    (r'\b(validate|verify|check|authenticate)\b', "VALIDATES"),
]
```

**Issue 4b: Missing Compound Relations**
- "5 failed login attempts within 15 minutes" should create:
  - (system, LOCKS, user_accounts)
  - (system, AFTER_CONDITION, failed_login_threshold)
  - (failed_login_threshold, HAS_VALUE, 5)
  - (failed_login_threshold, HAS_TIMEWINDOW, 15_minutes)

**Improvement:**
```python
# Extract quantitative constraints as separate entities
def _extract_quantitative_constraints(text: str) -> List[Dict]:
    # Pattern: "after X failed attempts within Y minutes"
    # Create: threshold entity with properties
    pass
```

---

#### 5. **Confidence Score Calibration**

**Issue 5a: Ceiling Effect**
- Multiple diverse requirements hit exactly 0.70
- No differentiation between "good" and "excellent" requirements
- BR-10 threshold (0.70) means many pass without distinction

**Analysis:**
```
Well-Written Security:     0.70 (has specific values, clear actors)
Banking Domain:            0.70 (specific amounts, timeframes)
Safety-Critical System:    0.70 (precise measurements)
IEEE 830 SRS Fragment:     0.70 (structured format)
```

**Improvement:**
```python
# Add bonus points for:
# - Multiple measurable thresholds (+0.05 each)
# - Clear actor-entity relationships (+0.03 each)
# - No weak modals (+0.05)
# - Domain-specific compliance mentioned (+0.02)
# Allow confidence to go up to 0.95 for exceptional requirements

# Penalize more heavily for:
# - Each HIGH severity ambiguity (-0.15 instead of -0.10)
# - Multiple MEDIUM ambiguities (compound effect)
# - Missing actors or systems (-0.05)
```

---

#### 6. **Enable LLaMA 3 Integration**

**Current State:** Using heuristic fallback only  
**Impact:** Lower accuracy on complex domain analysis

**Action Required:**
```bash
# 1. Get Groq API key from https://console.groq.com
# 2. Add to .env file:
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_TEMPERATURE=0.1

# 3. Restart server
```

**Expected Improvements with LLaMA 3:**
- Better entity classification (LLM understands context)
- More accurate ambiguity detection
- Domain-specific insights
- Better relation extraction
- Confidence scores up to 0.15-0.20 higher for clear requirements

---

#### 7. **Response Schema Enhancement**

**Current Schema:**
```python
class SemanticAnalysisResponse(BaseModel):
    id: str
    text: str
    entities: List[Dict]
    relations: List[Dict]
    ambiguities: List[Dict]
    confidence_score: float
    processed_at: datetime
```

**Recommended Schema:**
```python
class SemanticAnalysisResponse(BaseModel):
    id: str
    text: str
    method: str  # "llama3" or "heuristic_fallback"
    entities: List[Entity]
    relations: List[Relation]
    ambiguities: List[Ambiguity]
    confidence_score: float
    quality_grade: str  # "excellent", "good", "acceptable", "poor"
    suggestions: List[str]  # Top-level improvement suggestions
    processed_at: datetime
    processing_time_ms: int  # Performance metric

class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int
    description: str
    confidence: float  # Per-entity confidence
    inferred: bool = False  # True if not explicitly in text

class Ambiguity(BaseModel):
    term: str
    position: int
    description: str
    severity: str  # "high", "medium", "low"
    suggestion: str
    context: str
    category: str  # "vagueness", "incompleteness", "contradiction", etc.
```

---

#### 8. **Domain Classification**

**Missing Feature:** Automatic domain detection

**Improvement:**
```python
def _detect_domain(text: str) -> str:
    domain_keywords = {
        "healthcare": ["patient", "medical", "health", "clinical", "diagnosis"],
        "banking": ["transaction", "account", "bank", "payment", "financial"],
        "ecommerce": ["cart", "order", "product", "shipping", "refund"],
        "safety_critical": ["brake", "safety", "emergency", "alarm", "fail-safe"],
        "api": ["REST", "API", "endpoint", "JSON", "HTTP"],
        "general": []
    }
    
    # Count keyword matches and return dominant domain
    # Use this to apply domain-specific rules
```

**Benefits:**
- Apply domain-specific ambiguity checks
- Tailor confidence thresholds
- Generate domain-specific suggestions
- Better entity classification

---

#### 9. **Performance Metrics**

**Current:** No timing information  
**Recommended:** Add processing time tracking

```python
import time

def analyze_text(self, text: str) -> Dict[str, Any]:
    start_time = time.time()
    
    # ... analysis logic ...
    
    processing_time = time.time() - start_time
    result["processing_time_ms"] = int(processing_time * 1000)
    return result
```

**Target Metrics:**
- Heuristic mode: < 50ms per requirement
- LLaMA 3 mode: < 5 seconds per requirement
- Batch mode (10 requirements): < 500ms heuristic, < 30s LLM

---

#### 10. **Batch Analysis Endpoint**

**Current Limitation:** Single requirement per request  
**Improvement:** Add batch endpoint

```python
@router.post("/semantic/batch", response_model=BatchSemanticAnalysisResponse)
def analyze_semantic_batch(
    request: BatchSemanticAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze multiple requirements in one request"""
    results = []
    for req in request.requirements:
        result = semantic_analyzer.analyze_text(req.text)
        results.append(result)
    
    # Calculate aggregate statistics
    avg_confidence = sum(r["confidence_score"] for r in results) / len(results)
    total_ambiguities = sum(len(r["ambiguities"]) for r in results)
    
    return BatchSemanticAnalysisResponse(
        results=results,
        average_confidence=avg_confidence,
        total_ambiguities=total_ambiguities,
        processed_count=len(results)
    )
```

---

## Priority Recommendations

### 🔴 High Priority (Immediate Impact)
1. **Add `method` field to response** - 5 min fix
2. **Stop flagging "shall/must" as ambiguities** - Improves signal-to-noise
3. **Fix negative position values** - Prevents downstream errors
4. **Enable LLaMA 3 (get Groq API key)** - Biggest accuracy boost

### 🟡 Medium Priority (Significant Improvements)
5. **Enhance relation extraction** - Add more relation types
6. **Improve entity classification** - Better label accuracy
7. **Calibrate confidence scoring** - Remove ceiling effect
8. **Add domain classification** - Enables smart analysis

### 🟢 Low Priority (Nice to Have)
9. **Enhanced response schema** - Better structure, more metadata
10. **Batch endpoint** - Performance optimization
11. **Processing time metrics** - Monitoring and optimization

---

## Test Case Quality Analysis

### What Makes a "Good" Requirement (Based on Tests)

| Characteristic | Present in High-Score (0.70) | Missing in Low-Score (0.23-0.45) |
|----------------|------------------------------|-----------------------------------|
| **Specific Values** | ✅ "5 attempts", "15 minutes", "$10,000" | ❌ "fast", "many", "appropriate" |
| **Clear Modals** | ✅ "shall", "must" | ❌ "should", "may", "usually" |
| **Defined Actors** | ✅ "users", "medical staff", "customers" | ❌ Implicit or missing |
| **Measurable Criteria** | ✅ "50ms", "100%", "10 meters" | ❌ "good", "user-friendly" |
| **Explicit Actions** | ✅ "lock accounts", "sound alarm" | ❌ "be fast", "handle high traffic" |
| **Time Constraints** | ✅ "within 15 minutes", "2 business days" | ❌ "timely", "reasonable" |

### Formula for Well-Written Requirements:
```
[Actor/System] + [shall/must] + [specific action] + [measurable criteria] + [timeframe/constraint]

Example: "The system shall lock user accounts after 5 failed login attempts within 15 minutes"
         ↓ Actor: system
         ↓ Modal: shall
         ↓ Action: lock user accounts
         ↓ Criteria: 5 failed attempts
         ↓ Timeframe: within 15 minutes
```

---

## Next Steps

1. **Get Groq API key** and test with LLaMA 3
2. **Implement high-priority fixes** (method field, ambiguity filtering)
3. **Re-run tests** to measure improvements
4. **Add integration tests** to prevent regression
5. **Consider batch endpoint** for production use

---

## Files Modified/Created

- `/backend/test_semantic.py` - Test script (created)
- `/backend/semantic_test_results.json` - Full test results (created)
- `/backend/api/analysis.py` - Needs schema update
- `/backend/services/ai/semantic_analyzer.py` - Needs improvements listed above

---

## Questions for Consideration

1. Should we integrate LLaMA 3 via Groq API for higher accuracy?
2. Do we need batch analysis for production use cases?
3. Should we add domain-specific analysis rules?
4. Is the BR-10 threshold (0.70) appropriate, or should it be adjusted?
5. Do we need to support multiple requirement standards (IEEE 830, Volere, etc.)?
