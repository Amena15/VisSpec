# VisSpec - Visual LLM-Powered Requirements Validator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)
![LLaMA 3](https://img.shields.io/badge/LLaMA-3-orange.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)
![License](https://img.shields.io/badge/License-Academic-red.svg)

**FYP01-SE-T2530-393 | Multimedia University, Malaysia | 2026**

</div>

---

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Academic Justification](#academic-justification)
- [Author](#author)
- [License](#license)

---

## 📖 Overview

**VisSpec** (Visual Specification) is an AI-powered web application that validates software requirements documents (SRS, SDS, STS) using **Large Language Models (LLaMA 3 via Groq API)** and automatically generates **UML behavioral diagrams** to visualize system behavior.

The system performs:
- 🔍 **Semantic Analysis** - Extracts entities, relationships, and detects ambiguities
- ⚠️ **Predictive Analysis** - Estimates complexity, effort (hours), and risk levels
- 📝 **Validation Pipeline** - Detects inconsistencies, incompleteness, and contradictions
- 📊 **Diagram Generation** - Creates Use Case, Sequence, and Activity diagrams (Mermaid.js)
- 📄 **PDF Report Export** - Generates professional validation reports with watermark

---

## ✨ Features

### Core Capabilities

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Semantic Analysis** | Extract entities, actors, modal verbs, and ambiguities using LLaMA 3 | `/api/analysis/semantic` |
| **Predictive Analysis** | Complexity scoring, effort estimation, risk assessment | `/api/analysis/predictive` |
| **Full Analysis** | Combined semantic + predictive analysis | `/api/analysis/full` |
| **UML Diagram Generation** | Create Use Case, Sequence, and Activity diagrams from requirements | `/api/visualization/` (with `diagram_type` field) |
| **Document Validation** | Single and batch validation of requirement texts | `/validate/*` |
| **PDF Report Export** | Export validation reports as PDF with VisSpec watermark | `/export-report/{project_id}` |

### Analysis Pipeline

```
Text Input → spaCy NLP → LLaMA 3 (Groq) → Structured Output
                ↓              ↓
         Entity/Actor      Ambiguity/
         Extraction        Inconsistency Detection
                ↓              ↓
         Confidence Scoring → Validation Report
```

### User Roles

| Role | Capabilities |
|------|--------------|
| **Analyst** | Upload documents, run validation, generate diagrams, export reports, manage projects |
| **Supervisor** | Review projects, approve/reject deliverables, provide feedback, user management |

### Security

- 🔐 **JWT Authentication** - HS256 algorithm with configurable expiration
- 🔑 **bcrypt Password Hashing** - Industry-standard adaptive hash function with work factor
- 🛡️ **Rate Limiting** - 5 failed login attempts → 15-minute lockout
- 🔒 **Input Validation** - Pydantic schemas for request/response validation
- 🚫 **SQL Injection Prevention** - SQLAlchemy ORM with parameterized queries

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT (Browser)                                   │
│                     React 18 + Vite + Tailwind CSS                          │
│                          Port: 3000 (dev)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend (Port 8000)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Auth Router │  │ Analysis     │  │ Validation   │  │   Users      │    │
│  │  /auth/*     │  │ /api/analysis│  │ /validate    │  │  /api/users  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐                                        │
│  │Visualization │  │  Reports     │                                        │
│  │/api/viz/*    │  │ /export-report│                                        │
│  └──────────────┘  └──────────────┘                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INTELLIGENCE LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   spaCy NLP     │  │   LLaMA 3 (70B) │  │   scikit-learn              │ │
│  │   Tokenisation  │──│   Groq API      │──│   Complexity scoring        │ │
│  │   Entities      │  │   temp 0.1      │  │   Effort estimation         │ │
│  │   Modal verbs   │  │   few-shot      │  │   Risk classification       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER (SQLite + SQLAlchemy ORM)                    │
│  Users | Projects | Requirements | Defects | Diagrams | Traceability       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Boundaries

| Service | Responsibility | Files |
|---------|----------------|-------|
| **Authentication Service** | JWT tokens, bcrypt hashing, rate limiting, password reset | `api/auth.py`, `utils/security.py` |
| **Semantic Analysis Service** | Entity extraction, ambiguity detection, relationship mapping | `services/ai/semantic_analyzer.py` |
| **Predictive Analysis Service** | Complexity scoring, effort estimation, risk assessment | `services/ai/predictive_analyzer.py` |
| **Validation Service** | Completeness, consistency, ambiguity checks | `services/validation/*` |
| **Visualization Service** | Mermaid.js diagram generation (usecase/sequence/activity) | `services/visualization/visualizer.py` |
| **Report Service** | PDF export with watermark | `services/report/*` |

---

## 💻 Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Runtime |
| FastAPI | 0.115.0 | Web framework with async support |
| SQLAlchemy | 2.0.32 | ORM for database operations |
| SQLite | 3 | Lightweight, portable database |
| LLaMA 3 | 70B via Groq API | LLM for semantic analysis |
| spaCy | 3.7+ | NLP preprocessing (en_core_web_sm) |
| Passlib | 1.7.4 | Password hashing (bcrypt scheme) |
| python-jose | 3.3+ | JWT token creation/verification |
| Pydantic | 2.7+ | Request/response schema validation |
| ReportLab | 4.0+ | PDF report generation |
| scikit-learn | 1.4+ | Complexity and risk scoring |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18 | Component-based UI framework |
| Vite | 5 | Fast build tool and dev server |
| Tailwind CSS | 3 | Utility-first CSS framework |
| Axios | 1.6 | HTTP client for API calls |
| Mermaid.js | 10 | Diagram rendering engine |
| React Router | 6 | Client-side routing |

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- npm or yarn
- Git

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Amena15/VisSpec.git
cd VisSpec/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy English model
python -m spacy download en_core_web_sm

# Copy environment configuration
cp .env.example .env

# Edit .env with your Groq API key (see Configuration section)
nano .env  # or use your preferred editor

# Start backend server
python main.py
```

Backend will be available at: **http://localhost:8000**

### Frontend Setup

```bash
# Open new terminal
cd VisSpec/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

### Seed Test Users (Optional)

```bash
cd VisSpec/backend
source venv/bin/activate
python scripts/seed_users.py
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

Create a `.env` file in the `backend/` directory (copy from `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `True` | Enable debug mode (disable in production) |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Backend server port |
| `DATABASE_URL` | `sqlite:///./vispec.db` | Database connection string |
| `SECRET_KEY` | *(required)* | JWT signing key (min 32 chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT token expiration time |
| `GROQ_API_KEY` | *(required)* | Groq API key for LLaMA 3 access |
| `GROQ_MODEL` | `llama3-70b-8192` | LLM model identifier |
| `GROQ_TEMPERATURE` | `0.1` | LLM creativity (lower = more deterministic) |
| `GROQ_MAX_RETRIES` | `3` | Max retry attempts for API calls |
| `MAX_LOGIN_ATTEMPTS` | `5` | Failed attempts before lockout |
| `LOCKOUT_DURATION_MINUTES` | `15` | Account lockout duration |
| `MAX_FILE_SIZE_BYTES` | `10485760` | Max upload size (10MB) |
| `MAX_PAGES` | `50` | Max pages per document |
| `MIN_CONFIDENCE_THRESHOLD` | `0.70` | Minimum confidence for validation |
| `REPORT_WATERMARK` | `VisSpec` | Watermark text for PDF reports |

### Getting a Groq API Key

1. Visit [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to **API Keys** in the dashboard
4. Click **Create API Key**
5. Copy the generated key to `GROQ_API_KEY` in your `.env` file

> ⚠️ **SECURITY WARNING:** The default `SECRET_KEY` in `config.py` is for **development only**.  
> In any production-like environment, you **MUST** override it with a strong, random key in your `.env` file.

> ℹ️ **Note:** If `GROQ_API_KEY` is not provided, the system automatically falls back to a **rule-based heuristic** for semantic analysis. The heuristic has lower accuracy but ensures the system remains functional without an internet connection or API key.

---

## 📖 Usage

### Demo Credentials

After running the seed script (`python scripts/seed_users.py`):

#### Analyst Accounts (4 users)

| Username | Email | Password |
|----------|-------|----------|
| analyst | `analyst@vispec.com` | `VisSpec123` |
| john_doe | `john.doe@vispec.com` | `Analyst@2026` |
| jane_smith | `jane.smith@vispec.com` | `Analyst@2026` |
| ahmad_ali | `ahmad.ali@vispec.com` | `Analyst@2026` |

#### Supervisor Accounts (2 users)

| Username | Email | Password |
|----------|-------|----------|
| supervisor | `supervisor@vispec.com` | `VisSpec123` |
| dr_zarina | `zarina@vispec.com` | `Supervisor@2026` |

> ⚠️ **Note**: Login uses **email** and **password**, not username.

### Workflow

1. **Login** with your credentials at `http://localhost:3000`
2. **Analyst Dashboard** - Enter requirements text or upload documents
3. **Run Analysis** - Choose semantic, predictive, or full analysis
4. **View Results** - Examine detected ambiguities, inconsistencies, and complexity scores
5. **Generate Diagrams** - Create Use Case, Sequence, or Activity diagrams
6. **Export Report** - Download a PDF validation report with all findings

### API Usage Examples

#### Semantic Analysis

```bash
curl -X POST 'http://localhost:8000/api/analysis/semantic' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "The system shall allow users to register with email and password."
  }'
```

#### Predictive Analysis

```bash
curl -X POST 'http://localhost:8000/api/analysis/predictive' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "User authentication module with JWT, role-based access control, and session management."
  }'
```

#### Generate Use Case Diagram

```bash
curl -X POST 'http://localhost:8000/api/visualization/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "text": "Customers can browse products and checkout. Admins can manage products and view orders.",
    "diagram_type": "usecase"
  }'
```

---

## 📡 API Endpoints

### Authentication (`/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user (analyst/supervisor) | No |
| POST | `/auth/login` | Login with email/password → returns JWT | No |
| GET | `/auth/profile` | Get current user profile | Yes |
| POST | `/auth/change-password` | Change current password | Yes |
| POST | `/auth/forgot-password` | Request password reset email | No |
| POST | `/auth/reset-password` | Reset password with token | No |
| POST | `/auth/verify-reset-token` | Verify password reset token validity | No |

### Analysis (`/api/analysis`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/analysis/semantic` | Semantic analysis (entities, ambiguities, relationships) | Yes |
| POST | `/api/analysis/predictive` | Predictive analysis (complexity, effort, risk) | Yes |
| POST | `/api/analysis/full` | Combined semantic + predictive analysis | Yes |

### Visualization (`/api/visualization`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/visualization/` | Generate UML diagram (provide `diagram_type`: `usecase`/`sequence`/`activity` in JSON body) | Yes |

### Validation (`/validate`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/validate/validate` | Validate single requirement text | Yes |
| POST | `/validate/validate-batch` | Batch validate multiple requirements | Yes |

### Users (`/api/users`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/users/` | List all users (supervisor only) | Yes (Supervisor) |
| GET | `/api/users/{user_id}` | Get user by ID | Yes |
| PUT | `/api/users/{user_id}` | Update user details | Yes |
| DELETE | `/api/users/{user_id}` | Delete user (supervisor only) | Yes (Supervisor) |
| GET | `/api/users/settings` | Get current user settings | Yes |
| PUT | `/api/users/settings` | Update current user settings | Yes |

### Reports (`/export-report`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/export-report/export` | Export validation report as PDF | Yes |

> 💡 **Interactive API Documentation**: Available at `http://localhost:8000/docs` (Swagger UI)

---

## 🧪 Testing

### Backend Tests

```bash
cd VisSpec/backend
source venv/bin/activate
python -m pytest tests/ -v
```

### Test Coverage

| Test File | Coverage Area |
|-----------|---------------|
| `test_auth_fixed.py` | Authentication (register, login, token validation) |
| `test_auth_integration.py` | End-to-end authentication flows |
| `test_semantic_analyzer.py` | Entity extraction, ambiguity detection |
| `test_predictive_analyzer.py` | Complexity scoring, effort estimation |
| `test_visualizer.py` | Mermaid diagram syntax generation |

### Running Specific Tests

```bash
# Run only auth tests
python -m pytest tests/test_auth_fixed.py -v

# Run with coverage
python -m pytest tests/ --cov=services --cov=api --cov-report=term-missing
```

---

## 📁 Project Structure

```
VisSpec/
├── backend/                          # FastAPI backend (63+ files)
│   ├── api/                          # API route definitions (6 routers)
│   │   ├── analysis.py               # Semantic & predictive analysis endpoints
│   │   ├── auth.py                   # Authentication & password reset
│   │   ├── reports.py                # PDF report export
│   │   ├── users.py                  # User management (CRUD)
│   │   ├── validation.py             # Requirement validation
│   │   └── visualization.py          # UML diagram generation
│   ├── core/                         # Core configuration
│   │   └── config.py                 # Singleton settings (env vars)
│   ├── models/                       # SQLAlchemy ORM models (17 tables)
│   │   ├── user.py                   # User model with bcrypt hashing
│   │   ├── auxiliary.py              # Token, session, reset models
│   │   └── ...                       # Project, requirement, defect models
│   ├── schemas/                      # Pydantic request/response schemas
│   ├── services/                     # Business logic implementation
│   │   ├── ai/                       # AI/ML services
│   │   │   ├── semantic_analyzer.py  # LLaMA 3 + spaCy integration
│   │   │   ├── predictive_analyzer.py # Complexity/risk estimation
│   │   │   └── prompts.py            # LLM prompt templates
│   │   ├── validation/               # Validation pipeline
│   │   │   ├── completeness_analyzer.py
│   │   │   ├── consistency_checker.py
│   │   │   └── ambiguity_detector.py
│   │   ├── visualization/            # Diagram generation
│   │   │   └── visualizer.py         # Mermaid.js generator
│   │   └── report/                   # PDF export service
│   ├── utils/                        # Utility functions
│   │   └── security.py               # JWT, bcrypt, rate limiting
│   ├── scripts/                      # Database seeding & migration
│   │   ├── seed_users.py             # Create test users
│   │   └── populate_test_users.py    # Alternative seeding script
│   ├── tests/                        # Unit & integration tests
│   ├── config/                       # Database & environment config
│   ├── main.py                       # FastAPI application entry point
│   ├── requirements.txt              # Python dependencies
│   └── .env.example                  # Environment variable template
├── frontend/                         # React frontend (49+ files)
│   ├── src/
│   │   ├── components/               # Reusable UI components
│   │   ├── pages/                    # Route/page components
│   │   ├── services/                 # API service functions (Axios)
│   │   ├── context/                  # React context (theme, auth)
│   │   └── utils/                    # Helper functions
│   └── package.json                  # NPM dependencies
├── tests/                            # Root-level test directory
│   └── unit/                         # Unit tests for services
├── docs/                             # Project documentation
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

---

## 📚 Academic Justification

### Why This Architecture?

| Decision | Justification | Report Reference |
|----------|---------------|------------------|
| **Modular Monolith** | Avoids microservice complexity while maintaining clear service boundaries | Section 4.1, 5.2 |
| **LLaMA 3 (70B)** | State-of-the-art open LLM for semantic validation via Groq's fast inference | Section 4.8.1 |
| **FastAPI** | Native async support for non-blocking LLM API calls, automatic OpenAPI docs | Section 5.4.2 |
| **bcrypt Hashing** | Industry-standard adaptive hash with configurable work factor | REQ_01 (Table 3.2) |
| **0.70 Confidence Threshold** | Balances precision/recall for requirement validation (BR-10) | Section 2.3.3 |
| **SQLite** | Zero-configuration, portable database ideal for FYP demonstration | Section 5.4.3 |
| **Mermaid.js** | Text-to-diagram tool enabling dynamic UML generation from requirements | Section 4.8.2 |

### Requirements Implementation

| Report Section | Implementation Status |
|----------------|----------------------|
| Functional Requirements (REQ_01-20) | ✅ All implemented |
| Non-Functional (NFR_PS1-3, SP1-3, AR1-3, U1-3) | ✅ All addressed |
| Use Case Diagram (12 use cases) | ✅ All implemented |
| AI Model Design (LLaMA 3 + spaCy + scikit-learn) | ✅ Hybrid pipeline |
| Technology Stack | ✅ As specified in report |

---

## 👤 Author

**Mohammed Aamena Mohammed Abdulkarem**

| Detail | Information |
|--------|-------------|
| **Student ID** | 1221305728 |
| **Program** | Bachelor of Computer Science (Software Engineering) |
| **University** | Faculty of Computing and Informatics, Multimedia University, Malaysia |
| **Supervisor** | Dr. Zarina Binti Che Embi |
| **Project Code** | FYP01-SE-T2530-393 |
| **Academic Year** | 2026 |

---

## 📄 License

© 2026 Mohammed Aamena Mohammed Abdulkarem. All Rights Reserved.

This project is submitted in partial fulfillment of the requirements for the degree of **Bachelor of Computer Science (Software Engineering)** at Multimedia University, Malaysia.

---

## 🙏 Acknowledgements

- **Dr. Zarina Binti Che Embi** - Project supervision and guidance
- **Faculty of Computing and Informatics** - Academic support and resources
- **Groq** - High-performance LLM inference API
- **Open Source Community** - FastAPI, React, spaCy, Mermaid.js

---

## 📧 Contact

For questions regarding this project:

- **GitHub**: [@Amena15](https://github.com/Amena15)
- **Repository**: [github.com/Amena15/VisSpec](https://github.com/Amena15/VisSpec)

---

<div align="center">
  <sub>Built with ❤️ for FYP01-SE-T2530-393 | Multimedia University 2026</sub>
</div>
