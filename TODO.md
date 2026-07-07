# TODO

## 6.4 Diagram Mapping / Requirements linked to diagrams / Diagram nodes clickable retrieve from db

### Step 1: Repo inspection (done)
- Read:
  - backend/api/diagrams.py
  - backend/api/traceability.py
  - backend/models/diagram.py
  - backend/models/traceability.py
  - frontend/src/pages/Traceability.jsx

### Step 2: Backend implementation
- Add endpoint in `backend/api/diagrams.py` (diagrams router):
  - `GET /diagram/{diagram_id}/elements/{element_id}/requirements`
- Implement DB lookup:
  - find `DiagramElement` by `element_id` and use `source_req_id`
  - fetch linked `Requirement` and return fields compatible with traceability UI
- Reuse existing note/complexity/visual element logic from `backend/api/traceability.py` (or refactor into shared helpers if needed)

### Step 3: Frontend wiring
- Locate the actual diagram rendering UI (may be in another page/component not currently identified)
- Make diagram nodes clickable and store clicked element_id
- Call backend endpoint and show returned requirements (reuse existing modals/table UX)

### Step 4: Tests & smoke
- Add/extend backend tests for node-click requirements endpoint
- Run `pytest`
- Manual smoke test: generate diagram → click node → ensure requirements load

