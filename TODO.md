# VisSpec Analysis Flow Fixes
## Status: In Progress

### Step 1: [ ] Improve DOCX parsing in parser.py
- Per-paragraph cleaning to fix 'willwill'
- Apply sanitize_text early

### Step 2: [x] Auto-organize in documents.py upload
- Call requirement_organizer.enrich after saving reqs
- Transaction safety

### Step 3: [x] Frontend auto-trigger in AnalysisResults.jsx
- >90% uncategorized -> auto organize
- Prevent loops

### Step 4: [ ] Check requirement.py model defaults
- category default='functional'

### Step 5: [ ] Test & Restart servers
- Upload SRS.txt/docx
- Verify organized on load
- Run validation

**Next:** Step 1 - read files for parser.py edit.

