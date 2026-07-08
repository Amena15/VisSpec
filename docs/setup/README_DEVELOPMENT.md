# VisSpec Development Guide

## Project Overview
VisSpec is a comprehensive requirements specification and validation system that helps teams:
- Upload and analyze requirement documents
- Extract and organize requirements
- Generate UML diagrams (Use Case, Sequence, Activity)
- Validate requirements with AI-powered analysis
- Manage traceability matrices
- Generate comprehensive reports

## Architecture
- **Backend**: FastAPI with PostgreSQL database
- **Frontend**: Vue.js 3 with Tailwind CSS
- **AI Integration**: Groq API with LLaMA 3 for validation
- **Document Processing**: PyMuPDF, python-docx for text extraction

## Development Setup

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Database Setup
```bash
cd backend
python run_migration.py
```

## Key Features Implemented

### Module 2: Document Processing ✅
- **File Upload**: Supports PDF, DOCX, TXT files
- **Text Extraction**: PyMuPDF for PDFs, python-docx for DOCX
- **OCR Fallback**: pytesseract for scanned PDFs
- **Requirement Extraction**: Advanced pattern matching for modal verbs
- **Structure Identification**: Section headers and organization
- **Storage Management**: User quota tracking and enforcement

### Module 3: AI-Based Validation 🔄
- **LLM Integration**: Groq API with LLaMA 3
- **Defect Detection**: Ambiguity, Incompleteness, Inconsistency, Unverifiable
- **Confidence Scoring**: 70% threshold for reporting
- **Zero-Retention**: No data stored by AI provider

### Module 4: Diagram Generation ✅
- **Use Case Diagrams**: Mermaid and PlantUML formats
- **Sequence Diagrams**: BR-12 compliance (max 15 steps)
- **Activity Diagrams**: Process flow visualization
- **BR-11 Compliance**: No hallucinated actors

### Module 5: Traceability Management ✅
- **Traceability Matrix**: Requirement relationships
- **Impact Analysis**: Change impact assessment
- **Notes Management**: Add/edit/delete traceability notes
- **Export Capabilities**: Excel, CSV formats

## Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
cd backend
python tests/integration/test_documents_pipeline.py
python tests/integration/test_yousef_pipeline.py
```

## File Organization

### Backend Structure
```
backend/
├── api/                    # API endpoints
├── models/                 # Database models
├── services/               # Business logic
├── config/                 # Configuration
├── tests/                  # Test suite
├── temp_tests/            # Temporary test scripts (cleanup)
├── debug_logs/            # Debug logs (cleanup)
└── test_documents/        # Test documents
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/       # Reusable components
│   ├── pages/           # Page components
│   ├── services/        # API services
│   └── contexts/        # Vue contexts
├── tests/               # Test suite
├── temp_logs/          # Temporary logs (cleanup)
└── dist/               # Build output
```

## Business Rules Compliance

### BR-07: File Types ✅
- Only accepts PDF, DOCX, TXT files

### BR-08: File Size ✅
- Maximum 10MB file size limit

### BR-10: Confidence Threshold ✅
- 70% confidence score for defect reporting

### BR-11: Actor Compliance ✅
- No hallucinated actors in diagrams

### BR-12: Step Limit ✅
- Maximum 15 steps in sequence diagrams

## Recent Fixes Applied

### Document Processing Pipeline
- Fixed requirement extraction (was showing 0 requirements)
- Removed interfering TextCleaner preprocessing
- Enhanced pattern matching for modal verbs
- Improved OCR fallback for scanned PDFs

### Authentication Integration
- Fixed API endpoint paths (added /api prefix)
- Corrected role enum comparisons
- Enhanced error handling

### Test Suite
- Created comprehensive test coverage
- Fixed failing integration tests
- Added frontend test suite

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use Vue 3 Composition API
- Implement proper error handling
- Add comprehensive logging

### Database
- Use SQLAlchemy ORM
- Implement proper migrations
- Add foreign key constraints
- Use UUID for primary keys

### API Design
- RESTful endpoints with /api prefix
- Proper HTTP status codes
- Pydantic models for validation
- Comprehensive error messages

### Testing
- Unit tests for all services
- Integration tests for workflows
- Frontend component tests
- End-to-end testing

## Deployment Notes

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost/vispec
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key
```

### Production Build
```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Common Issues
1. **Requirements Found: 0** - Restart backend server after changes
2. **Database Connection** - Check PostgreSQL is running
3. **API Errors** - Verify /api prefix in requests
4. **OCR Not Working** - Install pytesseract and PIL

### Debug Commands
```bash
# Check backend logs
tail -f backend/backend.log

# Test document parsing
python backend/test_current_parser.py

# Run specific tests
python -m pytest backend/tests/test_documents.py -v
```
