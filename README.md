# VisSpec - Visual Specification System

VisSpec is an AI-powered system for converting textual requirements into visual specifications. The system analyzes requirements documents using natural language processing and generates visual diagrams to help stakeholders better understand system specifications.

## Architecture Overview

VisSpec follows a modular monolith architecture with clear service boundaries:

- **Frontend**: React.js with Vite and Tailwind CSS
- **Backend**: Python 3.10+ with FastAPI
- **AI Services**: spaCy for NLP and LLaMA 3 for advanced analysis
- **Database**: SQLite for simplicity and portability
- **Visualization**: Mermaid.js for diagram generation

## Features

- **Semantic Analysis**: Extract entities, relationships, and ambiguities from text
- **Predictive Analysis**: Estimate complexity, effort, and risk levels
- **Visualization Generation**: Create UML diagrams from requirements text
- **Role-Based Access Control**: Different interfaces for analysts and supervisors
- **JWT Authentication**: Secure token-based authentication

## System Requirements

- Python 3.10+
- Node.js 18+
- npm or yarn

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd VisSpec/backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install spaCy English model:
```bash
python -m spacy download en_core_web_sm
```

5. Start the backend server:
```bash
python main.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd VisSpec/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

## Usage

1. Access the application at `http://localhost:3000`
2. Register a new account or use demo credentials:
   - Analyst: `analyst` / `password`
   - Supervisor: `supervisor` / `password`
3. Use the Analyst Dashboard to analyze requirements text
4. Generate visualizations from the Visualization page

## API Documentation

The API documentation is available at `/docs` when the backend is running.

## Testing

Run backend tests:
```bash
cd VisSpec/backend
python -m pytest tests/
```

## Architecture Details

### Service Boundaries
- **Authentication Service**: Handles user authentication and authorization
- **Analysis Service**: Performs semantic and predictive analysis
- **Visualization Service**: Generates diagrams from text
- **Document Service**: Manages document storage and retrieval

### Security Measures
- JWT-based authentication
- Input validation and sanitization
- Role-based access control
- SQL injection prevention

### Non-Functional Requirements
- Performance: Async handling with FastAPI
- Maintainability: Clear separation of concerns
- Scalability: Stateless design ready for horizontal scaling
- Security: Multiple layers of protection
- Testability: Comprehensive test suite
- Usability: Intuitive role-based interfaces
- Portability: SQLite database for easy deployment
- Reliability: Error handling and logging

## Project Structure

```
VisSpec/
├── backend/
│   ├── api/           # API route definitions
│   ├── models/        # Database models
│   ├── services/      # Business logic services
│   │   ├── ai/        # AI analysis services
│   │   └── visualization/ # Visualization services
│   ├── utils/         # Utility functions
│   ├── config/        # Configuration files
│   ├── schemas/       # Pydantic schemas
│   └── main.py        # Application entry point
├── frontend/
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/     # Page components
│   │   ├── services/  # API service functions
│   │   └── App.jsx    # Main application component
│   └── package.json   # Frontend dependencies
├── tests/             # Test files
└── README.md          # This file
```

## Academic Justification

This architecture balances professional software engineering practices with academic feasibility:

- **Modular Monolith**: Avoids complexity of distributed systems while maintaining clear service boundaries
- **Technology Stack**: Uses industry-standard tools appropriate for an FYP
- **AI Integration**: Demonstrates advanced NLP techniques without requiring complex infrastructure
- **Security**: Implements professional-grade security measures
- **Scalability**: Design allows for future expansion to microservices if needed

## License

This project is part of an academic submission and is intended for educational purposes.# Test commit to verify attribution
