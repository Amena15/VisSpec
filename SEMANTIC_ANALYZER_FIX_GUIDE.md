# 🔧 Implementation Guide: Fixing Semantic Analyzer
## How to Improve from 0% to 85%+ Accuracy

---

## 1. Problem Statement

**Current State**: Semantic analyzer returns empty `ambiguities: []` for all inputs
**Expected State**: Detect vague terms and return non-empty list with confidence scores
**Goal**: Achieve Precision ≥84.3%, Recall ≥78.1%, F1 ≥81.0%

---

## 2. Debugging Checklist

### 2.1 Is the Endpoint Working?

```bash
# Test the endpoint directly
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=analyst@vispec.com&password=VisSpec123" | jq -r '.access_token')

# Now test semantic analysis
curl -X POST http://localhost:8000/api/analysis/semantic \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The system shall be fast and user-friendly",
    "analysis_type": "semantic"
  }' | jq '.'
```

**Expected Response**:
```json
{
  "ambiguities": [
    {
      "term": "fast",
      "category": "vague_adjective",
      "confidence": 0.85,
      "suggestion": "Specify response time (e.g., within 200 milliseconds)"
    },
    {
      "term": "user-friendly",
      "category": "vague_adjective",
      "confidence": 0.82,
      "suggestion": "Define specific user experience metrics or criteria"
    }
  ]
}
```

**If you get empty `[]` ambiguities**, proceed to Section 2.2

### 2.2 Is the Analyzer Module Loaded?

**File to Check**: `backend/services/ai/semantic_analyzer.py` (or similar)

Look for these patterns:

```python
# ❌ MISSING - This should exist:
class SemanticAnalyzer:
    def __init__(self):
        self.vague_terms = {
            "fast": 0.85,
            "slow": 0.85,
            "user-friendly": 0.82,
            "adequate": 0.80,
            # ... more terms
        }
    
    def analyze(self, text: str) -> List[Dict]:
        """Detect vague terms in requirement text"""
        results = []
        for term, confidence in self.vague_terms.items():
            if term in text.lower():
                results.append({
                    "term": term,
                    "confidence": confidence,
                    "category": "vague_adjective"
                })
        return results
```

**If you don't see this class or similar**, it needs to be created or imported.

### 2.3 Is the Analyzer Instantiated?

**File to Check**: `backend/api/analysis.py` or wherever `/api/analysis/semantic` is defined

Look for:

```python
# ❌ MISSING - This should exist:
from services.ai.semantic_analyzer import SemanticAnalyzer

analyzer = SemanticAnalyzer()  # ← INSTANTIATE GLOBALLY

@router.post("/semantic")
async def analyze_semantic(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    results = analyzer.analyze(request.text)  # ← USE THE ANALYZER
    return {"ambiguities": results}
```

**If analyzer is not instantiated or called**, that's your bug.

---

## 3. Implementation Steps

### Step 1: Create/Update Semantic Analyzer Service

**File**: `backend/services/ai/semantic_analyzer.py`

```python
"""
Semantic Analyzer for Requirement Validation
Detects vague terms, weak modals, and ambiguous language patterns
"""

import re
from typing import List, Dict, Tuple
from enum import Enum

class DefectCategory(str, Enum):
    """Categories of requirement defects"""
    VAGUE_ADJECTIVE = "vague_adjective"
    WEAK_MODAL = "weak_modal"
    INDEFINITE_QUANTIFIER = "indefinite_quantifier"
    INCOMPLETE_SPECIFICATION = "incomplete_specification"

class SemanticAnalyzer:
    """Analyzes requirements for semantic defects according to IEEE 830"""
    
    def __init__(self):
        # Vague adjectives (high confidence = 0.80-0.90)
        self.vague_adjectives = {
            "fast": 0.85,
            "slow": 0.85,
            "quickly": 0.85,
            "slow": 0.85,
            "user-friendly": 0.82,
            "easy": 0.83,
            "simple": 0.82,
            "complex": 0.80,
            "adequate": 0.85,
            "appropriate": 0.85,
            "suitable": 0.83,
            "reliable": 0.80,  # Without metrics
            "robust": 0.80,
            "secure": 0.80,  # Without specific security measures
            "safe": 0.80,
            "efficient": 0.82,
            "effective": 0.82,
            "good": 0.90,
            "bad": 0.90,
            "better": 0.85,
            "worse": 0.85,
            "reasonable": 0.85,
            "convenient": 0.82,
            "useful": 0.80,
            "important": 0.80,
            "necessary": 0.80,
        }
        
        # Weak modals (confidence = 0.75-0.85)
        self.weak_modals = {
            "should": 0.80,
            "may": 0.82,
            "might": 0.82,
            "could": 0.80,
            "possibly": 0.85,
            "possibly": 0.85,
            "perhaps": 0.85,
            "attempt": 0.78,
            "try": 0.78,
            "usually": 0.80,
            "generally": 0.78,
            "tend": 0.78,
            "likely": 0.75,
            "can": 0.60,  # Lower confidence, common in specs
        }
        
        # Indefinite quantifiers (confidence = 0.85)
        self.indefinite_quantifiers = {
            "many": 0.85,
            "several": 0.85,
            "some": 0.85,
            "few": 0.85,
            "various": 0.85,
            "multiple": 0.75,  # Lower - sometimes acceptable with context
            "enough": 0.85,
            "little": 0.85,
            "lot": 0.85,
            "large": 0.80,
            "small": 0.80,
            "big": 0.80,
        }
        
        # Phrases that indicate incomplete specification
        self.incomplete_patterns = [
            (r"etc\.", 0.85, "incomplete_specification"),
            (r"and\s+so\s+on", 0.85, "incomplete_specification"),
            (r"as\s+appropriate", 0.80, "incomplete_specification"),
            (r"as\s+applicable", 0.80, "incomplete_specification"),
            (r"if\s+necessary", 0.80, "incomplete_specification"),
        ]
    
    def analyze(self, text: str) -> List[Dict]:
        """
        Analyze requirement text for semantic defects
        
        Args:
            text: Requirement statement to analyze
            
        Returns:
            List of detected ambiguities with confidence scores
        """
        if not text or not isinstance(text, str):
            return []
        
        results = []
        text_lower = text.lower()
        
        # Check vague adjectives
        for term, confidence in self.vague_adjectives.items():
            if self._word_boundary_match(text_lower, term):
                results.append({
                    "term": term,
                    "category": DefectCategory.VAGUE_ADJECTIVE.value,
                    "confidence": confidence,
                    "suggestion": f"Replace '{term}' with specific, measurable criteria",
                    "severity": "medium"
                })
        
        # Check weak modals
        for modal, confidence in self.weak_modals.items():
            if self._word_boundary_match(text_lower, modal):
                results.append({
                    "term": modal,
                    "category": DefectCategory.WEAK_MODAL.value,
                    "confidence": confidence,
                    "suggestion": f"Replace '{modal}' with mandatory requirement ('shall', 'must')",
                    "severity": "high"
                })
        
        # Check indefinite quantifiers
        for quantifier, confidence in self.indefinite_quantifiers.items():
            if self._word_boundary_match(text_lower, quantifier):
                results.append({
                    "term": quantifier,
                    "category": DefectCategory.INDEFINITE_QUANTIFIER.value,
                    "confidence": confidence,
                    "suggestion": f"Specify exact quantity or measurement instead of '{quantifier}'",
                    "severity": "medium"
                })
        
        # Check incomplete patterns
        for pattern, confidence, category in self.incomplete_patterns:
            if re.search(pattern, text_lower):
                match = re.search(pattern, text_lower)
                results.append({
                    "term": match.group(0),
                    "category": category,
                    "confidence": confidence,
                    "suggestion": "Complete the specification without ambiguous references",
                    "severity": "high"
                })
        
        # Deduplicate and sort by confidence
        results = self._deduplicate(results)
        results.sort(key=lambda x: x["confidence"], reverse=True)
        
        return results
    
    def _word_boundary_match(self, text: str, word: str) -> bool:
        """Check if word appears with word boundaries"""
        pattern = r'\b' + re.escape(word) + r'\b'
        return bool(re.search(pattern, text))
    
    def _deduplicate(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate detections, keeping highest confidence"""
        seen = {}
        for result in results:
            key = result["term"]
            if key not in seen or result["confidence"] > seen[key]["confidence"]:
                seen[key] = result
        return list(seen.values())
    
    def get_severity_score(self, results: List[Dict]) -> Tuple[float, str]:
        """
        Calculate overall severity score
        Returns: (score 0-1, severity_level)
        """
        if not results:
            return 0.0, "acceptable"
        
        avg_confidence = sum(r["confidence"] for r in results) / len(results)
        
        high_severity = sum(1 for r in results if r.get("severity") == "high")
        
        # Scoring: avg confidence + penalty for high severity
        score = min(avg_confidence + (high_severity * 0.1), 1.0)
        
        if score > 0.8:
            level = "critical"
        elif score > 0.6:
            level = "major"
        elif score > 0.4:
            level = "minor"
        else:
            level = "acceptable"
        
        return score, level

# Singleton instance
_analyzer = None

def get_analyzer() -> SemanticAnalyzer:
    """Get or create singleton analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = SemanticAnalyzer()
    return _analyzer
```

### Step 2: Update API Endpoint

**File**: `backend/api/analysis.py`

```python
"""Update the semantic analysis endpoint"""

from services.ai.semantic_analyzer import get_analyzer

@router.post("/semantic")
async def analyze_semantic(
    request: AnalysisRequest,  # Ensure this has 'text' field
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze requirement text for semantic defects
    Returns: List of detected ambiguities with confidence scores
    """
    try:
        # Validate input
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text field cannot be empty")
        
        if len(request.text) > 5000:
            raise HTTPException(status_code=400, detail="Text exceeds 5000 character limit")
        
        # Get analyzer and analyze
        analyzer = get_analyzer()
        ambiguities = analyzer.analyze(request.text)
        
        # Log analysis
        logger.info(
            f"Semantic analysis performed",
            extra={
                "user_id": current_user.user_id,
                "text_length": len(request.text),
                "defects_found": len(ambiguities)
            }
        )
        
        return {
            "status": "success",
            "ambiguities": ambiguities,
            "defects_found": len(ambiguities) > 0,
            "confidence_threshold": 0.70
        }
    
    except ValueError as e:
        logger.exception("Semantic analysis validation error", extra={
            "user_id": current_user.user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.exception("Semantic analysis failed", extra={
            "user_id": current_user.user_id,
            "error_type": type(e).__name__
        })
        raise HTTPException(
            status_code=500,
            detail="Analysis failed. Please try again or contact support."
        )
```

### Step 3: Verify Integration

**File**: `backend/api/analysis.py` or `main.py`

Ensure the analyzer is properly imported and available:

```python
# At the top of your analysis.py or main.py
from services.ai.semantic_analyzer import get_analyzer, SemanticAnalyzer

# Make sure the route is registered
@app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])
```

---

## 4. Testing the Fix

### 4.1 Manual Test

```bash
# Start backend
cd /Users/amena/Documents/FYPCode/VisSpec/backend
python main.py &
sleep 5

# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=analyst@vispec.com&password=VisSpec123" | jq -r '.access_token')

# Test semantic analyzer
curl -X POST http://localhost:8000/api/analysis/semantic \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The system shall be fast",
    "analysis_type": "semantic"
  }' | jq '.'
```

**Expected Output**:
```json
{
  "ambiguities": [
    {
      "term": "fast",
      "category": "vague_adjective",
      "confidence": 0.85,
      "suggestion": "Replace 'fast' with specific, measurable criteria",
      "severity": "medium"
    }
  ],
  "defects_found": true
}
```

### 4.2 Re-Run Full Evaluation

```bash
cd /Users/amena/Documents/FYPCode/VisSpec/backend
python evaluate_model.py
```

**Expected Improvements**:
```
Before:  Precision 0%, Recall 0%, F1 0%
After:   Precision 85-90%, Recall 80-85%, F1 82-87%
```

---

## 5. Performance Expectations

### 5.1 Estimated Accuracy After Fix

| Metric | Current | Expected After | Target |
|--------|---------|-----------------|--------|
| Precision | 0% | 85-92% | ≥84.3% ✅ |
| Recall | 0% | 80-88% | ≥78.1% ✅ |
| F1-Score | 0% | 82-90% | ~81.0% ✅ |

### 5.2 Response Time

Should remain <5ms per request (well within 30s target)

---

## 6. Troubleshooting

### Issue: Still getting 0% accuracy after fix

**Debugging steps:**
1. Verify analyzer is instantiated: `print(analyzer.vague_adjectives)` should print dict
2. Test analyzer directly: `analyzer.analyze("fast")` should return results
3. Check endpoint logs for errors
4. Verify authentication token is valid

### Issue: Very high false positive rate

**Solution:**
- Increase confidence threshold from 0.70 to 0.75 or 0.80
- Remove edge-case terms that are too common (e.g., "can")
- Refine term list to only high-confidence patterns

### Issue: Missing some defects

**Solution:**
- Add more terms to vague_adjectives dictionary
- Add regex patterns for compound phrases
- Implement phrase-level analysis instead of word-level

---

## 7. Next Optimization

After achieving target benchmarks, consider:

1. **ML-based Detection**: Train on larger dataset
2. **Context Analysis**: Consider surrounding words
3. **Domain-Specific Terms**: Add industry-specific terminology
4. **Multilingual Support**: Extend to other languages
5. **Custom Dictionaries**: Allow user-defined vague terms

---

## 8. Documentation

Don't forget to update your FYP report:

```markdown
### 4.8.1 Semantic Analyzer Implementation

The semantic analyzer identifies requirement defects by detecting:

1. **Vague Adjectives** (confidence 0.80-0.90): fast, slow, easy, adequate, etc.
2. **Weak Modals** (confidence 0.75-0.85): should, may, could, etc.
3. **Indefinite Quantifiers** (confidence 0.85): many, several, some, etc.
4. **Incomplete Specifications** (confidence 0.80-0.85): "etc.", "and so on", etc.

The analyzer achieves [XX]% precision and [XX]% recall on a test dataset 
of 20 IEEE 830 standard-compliant requirements.
```

---

**Ready to implement?** Start with Step 1 and test at each phase!
