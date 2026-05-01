# Requirements Classification Improvement Plan

## Overview
Improve the Requirements tab in Analysis Results (`/analysis-results/:id`) by:
1. Organizing requirements into modules with semantic IDs
2. Classifying requirements by category (functional, non_functional, etc.)
3. Extracting entities (actors, modal verbs, vague terms)
4. Linking classification with validation
5. Redesigning the frontend with badges, filters, and summary cards

## Critical Architecture Decision
**LLM processing is DECOUPLED from file upload** to prevent HTTP timeouts.
- Upload: Fast, saves raw requirements only
- Enrichment: Triggered separately from AnalysisResults page, runs LLM classification + organization

---

## Phase 1 — Backend: Add Database Columns & Schemas

### 1.1 `backend/models/requirement.py`
- Add columns: `category`, `category_confidence`, `semantic_id`, `module_name`
- These are nullable to support existing data

### 1.2 `backend/schemas/document.py`
- Update `RequirementItem` with: `category`, `category_confidence`, `semantic_id`, `module_name`, `actors`, `modal_verbs`, `vague_terms`

### 1.3 Database Migration
- Run migration to add new columns

---

## Phase 2 — Backend: Create Requirement Organizer Service

### 2.1 `backend/services/ai/requirement_organizer.py` (NEW)
Create a service that:
- Takes document text + raw requirements
- Groups requirements into logical modules (User Management, Authentication, etc.)
- Generates semantic IDs: FR-UM-01, NFR-SEC-01, etc.
- Standardizes text to "The system shall..." format
- Splits compound requirements into atomic ones
- Calls `llm_service.classify_requirements()` for category + confidence
- Calls `llm_service.extract_entities()` for actors, modal verbs, vague terms
- Returns fully enriched requirements

### 2.2 `backend/services/document/parser.py`
- Keep `parse_full()` fast — NO LLM calls
- Only extract raw text, structure, basic requirements

### 2.3 `backend/api/documents.py`
- Upload endpoint: stays fast, only saves raw requirements
- `get_document` endpoint: return all enriched fields in response

---

## Phase 3 — Backend: Create Enrichment API Endpoint

### 3.1 `backend/api/analysis.py`
- Add `POST /api/analysis/enrich/{doc_id}` endpoint
- Runs `requirement_organizer.organize_and_enrich()`
- Updates `Requirement` records in DB with enriched data
- Returns status/progress
- This is called from the AnalysisResults page after upload

---

## Phase 4 — Backend: Link Classification with Validation

### 4.1 `backend/services/validation/validator.py`
- Use classification data (vague_terms, modal_verbs) to enhance defect detection
- Better severity assessment based on category

### 4.2 `backend/api/validation.py`
- Map defects to specific requirements by text similarity
- Update per-requirement `validation_status` based on defects found

---

## Phase 5 — Frontend: Redesign Requirements Tab

### 5.1 `frontend/src/pages/AnalysisResults.jsx`
- Add "Run Organization & Classification" button when requirements are not yet enriched
- Show loading/progress state during enrichment
- Redesign Requirements tab with:
  - **Module grouping**: Collapsible sections by module name
  - **Semantic IDs**: Hierarchical IDs like FR-UM-01
  - **Category badges**: Color-coded (Functional=blue, Non-Functional=purple, Interface=green, Constraint=orange, Data=teal)
  - **Actors chips**: Small badges showing extracted actors
  - **Modal verbs**: Highlighted inline (shall, must, should, may)
  - **Vague terms warning**: Amber highlight when vague terms detected
  - **Category filter dropdown**: Filter by requirement type
  - **Search bar**: Search requirement text
  - **Expandable rows**: Show full details (confidence, all entities)
  - **Summary cards**: Total requirements, by category breakdown, with vague terms count

### 5.2 `frontend/src/services/api.js`
- Add `analysisAPI.enrichDocument(docId)` method
- Ensure document detail response includes all new fields

---

## Files to Create/Edit

### New Files
- `backend/services/ai/requirement_organizer.py`

### Modified Files
| File | Changes |
|------|---------|
| `backend/models/requirement.py` | Add `category`, `category_confidence`, `semantic_id`, `module_name` |
| `backend/schemas/document.py` | Add new fields to `RequirementItem` |
| `backend/services/document/parser.py` | Remove any LLM calls, keep fast |
| `backend/api/documents.py` | Return enriched fields; keep upload fast |
| `backend/api/analysis.py` | Add `POST /api/analysis/enrich/{doc_id}` endpoint |
| `backend/services/validation/validator.py` | Use classification data |
| `backend/api/validation.py` | Update per-requirement validation status |
| `frontend/src/services/api.js` | Add `analysisAPI.enrichDocument()` |
| `frontend/src/pages/AnalysisResults.jsx` | Complete redesign |

---

## Implementation Order
1. Add DB columns (`models/requirement.py`)
2. Update schemas (`schemas/document.py`)
3. Create `requirement_organizer.py` service
4. Update `parser.py` to stay fast
5. Update `documents.py` API
6. Add enrichment endpoint to `analysis.py`
7. Update validation to use classification data
8. Update frontend API service
9. Redesign AnalysisResults Requirements tab
10. Test end-to-end

---

## Current Progress Tracker

| Step | Status | Notes |
|------|--------|-------|
| Phase 1.1 - DB Columns | ✅ DONE | `requirement.py` updated |
| Phase 1.2 - Schemas | ✅ DONE | `document.py` schemas updated |
| Phase 2.1 - Organizer Service | ✅ DONE | `requirement_organizer.py` created |
| Phase 2.2 - Parser Fast | ✅ DONE | `parser.py` has no LLM calls |
| Phase 2.3 - Documents API | ✅ DONE | `documents.py` returns enriched fields |
| Phase 3 - Enrichment Endpoint | ✅ DONE | `analysis.py` enrich endpoint added |
| Phase 4.1 - Validator Context | ✅ DONE | `validator.py` enhanced with classification context |
| Phase 4.2 - Defect Mapping | ✅ DONE | `validation.py` maps defects by similarity + updates validation_status |
| Phase 5.1 - AnalysisResults UI | 🔄 USER | Frontend redesign (user implementing) |
| Phase 5.2 - Frontend API | ✅ DONE | `api.js` enrich method added |

