#!/usr/bin/env python3
"""Test all Pydantic schemas for VisSpec backend."""
import sys
import traceback
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Force reload of auth module to ensure we have the validators
import backend.schemas.auth
importlib.reload(backend.schemas.auth)
from backend.schemas.auth import UserCreate as AuthUserCreate
from backend.schemas.document import RequirementItem
from backend.schemas import *

print("Loading schemas (using reloaded auth)...")
try:
    from pydantic import ValidationError
    print("  ✓ Schemas imported successfully")
except Exception as e:
    print(f"❌ Failed to import schemas: {e}")
    traceback.print_exc()
    sys.exit(1)

def test_auth_schemas():
    print("\n🔐 Testing Auth Schemas...")
    
    # Token
    token = Token(access_token="abc123", token_type="bearer")
    assert token.access_token == "abc123"
    print("  ✓ Token")

    # TokenData
    td = TokenData(email="test@example.com", role="analyst")
    assert td.email == "test@example.com"
    print("  ✓ TokenData")

    # UserCreate valid (use reloaded class)
    user = AuthUserCreate(
        username="valid_user",
        email="good@example.com",
        password="StrongP@ss1",
        role="analyst"
    )
    assert user.username == "valid_user"
    print("  ✓ UserCreate (valid)")

    # Invalid username (too short)
    try:
        AuthUserCreate(
            username="ab",
            email="a@b.com",
            password="Test@123",
            role="analyst"
        )
        print("  ❌ Username validator missing")
        raise AssertionError("Username validation missing")
    except ValidationError as e:
        errors = e.errors()
        if any("Username must be at least 3 characters" in err.get("msg", "") for err in errors):
            print("  ✓ UserCreate (invalid username caught)")
        else:
            print(f"  ⚠️ Unexpected error: {errors}")
            raise

    # Invalid password (no special char, long enough)
    try:
        AuthUserCreate(
            username="user",
            email="a@b.com",
            password="Test12345",
            role="analyst"
        )
        print("  ❌ Password validator missing")
        raise AssertionError("Password validation missing")
    except ValidationError as e:
        errors = e.errors()
        if any("special character" in err.get("msg", "") for err in errors):
            print("  ✓ UserCreate (invalid password caught)")
        else:
            print(f"  ⚠️ Unexpected error: {errors}")
            raise

    # Rest of auth schemas (use regular imports, they are fine)
    UserLogin(username="user", password="pass")
    print("  ✓ UserLogin")
    PasswordReset(email="a@b.com", new_password="NewPass@1", token="tok123")
    print("  ✓ PasswordReset")
    PasswordChange(current_password="old", new_password="new")
    print("  ✓ PasswordChange")
    UserUpdate(username="new", email="new@ex.com", role="supervisor")
    print("  ✓ UserUpdate")
    UserResponse(
        user_id="123", username="tester", email="t@t.com",
        role="analyst", is_active=1, created_at="2025-01-01T00:00:00Z"
    )
    print("  ✓ UserResponse")

# Keep the rest of the test functions unchanged (they use the regular imports)
def test_user_schemas():
    print("\n👤 Testing User Schemas...")
    UserBase(username="base", email="base@ex.com", role="analyst")
    print("  ✓ UserBase")
    UserCreate(username="creator", email="cr@ex.com", password="Pass@123", role="supervisor")
    print("  ✓ UserCreate (from user.py)")
    UserUpdate(username="upd")
    print("  ✓ UserUpdate")
    UserResponse(user_id="u1", username="resp", email="r@r.com", role="analyst", is_active=1, created_at="now")
    print("  ✓ UserResponse")
    UserInDB(user_id="u2", username="indb", email="in@db.com", role="analyst", is_active=1, created_at="now", password_hash="$2b$12$...")
    print("  ✓ UserInDB")

def test_document_schemas():
    print("\n📄 Testing Document Schemas...")
    # Import RequirementItem directly (not exported in __init__)
    from backend.schemas.document import RequirementItem
    
    req = RequirementItem(req_id="r1", req_identifier="REQ-001", original_text="System shall login", current_text="System shall login", word_count=3)
    print("  ✓ RequirementItem")
    DocumentBase(filename="test.pdf", file_extension="pdf", file_size_bytes=5000)
    print("  ✓ DocumentBase")
    DocumentCreate(filename="test.pdf", file_extension="pdf", file_size_bytes=5000, project_id="proj-1")
    print("  ✓ DocumentCreate")
    DocumentUploadResponse(doc_id="d1", project_id="p1", filename="f.txt", file_extension="txt", file_size_bytes=100, word_count=50, status="uploaded", upload_date="now", requirements_found=5)
    print("  ✓ DocumentUploadResponse")
    DocumentSummary(doc_id="d2", project_id="p2", filename="s.pdf", file_extension="pdf", file_size_bytes=200, word_count=100, status="processed", upload_date="now", quality_score=85.5)
    print("  ✓ DocumentSummary")
    DocumentDetail(doc_id="d3", project_id="p3", filename="detail.pdf", file_extension="pdf", file_size_bytes=300, word_count=150, status="validated", upload_date="now", requirements=[req])
    print("  ✓ DocumentDetail")
    DocumentDeleteResponse(message="deleted", doc_id="d4", deleted_requirements=10)
    print("  ✓ DocumentDeleteResponse")


def test_validation_schemas():
    print("\n🔍 Testing Validation Schemas...")
    ValidationRequest(text="text")
    print("  ✓ ValidationRequest")
    DocumentValidationRequest(doc_id="doc123", project_id="proj456")
    print("  ✓ DocumentValidationRequest")
    DefectResponse(text="Ambiguous", type="ambiguity", severity="high", confidence=0.95, description="desc")
    print("  ✓ DefectResponse")
    ValidationResponse(overall_score=78.5, total_defects=3, defects_by_type={}, defects_by_severity={}, defects=[], llm_used=True, processing_time_ms=1200)
    print("  ✓ ValidationResponse")
    DocumentValidationResponse(validation_id="val1", doc_id="doc1", status="completed")
    print("  ✓ DocumentValidationResponse")

def test_traceability_schemas():
    print("\n🔗 Testing Traceability Schemas...")
    TraceabilityEntry(matrix_id="m1", project_id="p1", req_id="r1", validation_status="passed", updated_at="now")
    print("  ✓ TraceabilityEntry")
    TraceabilityNoteCreate(req_id="r1", project_id="p1", content="note")
    print("  ✓ TraceabilityNoteCreate")
    TraceabilityNoteResponse(note_id="n1", req_id="r1", project_id="p1", content="c", note_type="t", is_resolved=0, created_at="now")
    print("  ✓ TraceabilityNoteResponse")

def test_visualization_schemas():
    print("\n📊 Testing Visualization Schemas...")
    from backend.schemas.visualization import Relationship
    
    rel = Relationship(from_="User", to="Login", type="association")
    print("  ✓ Relationship")
    VisualizationRequest(text="User can login", diagram_type="usecase")
    print("  ✓ VisualizationRequest")
    VisualizationResponse(id="viz1", diagram_type="usecase", mermaid_syntax="", plantuml_syntax="", title="", description="", generated_at="now")
    print("  ✓ VisualizationResponse")

def test_analysis_schemas():
    print("\n📈 Testing Analysis Schemas...")
    from datetime import datetime, timezone
    
    now_str = datetime.now(timezone.utc).isoformat()
    
    # SemanticAnalysisRequest
    sreq = SemanticAnalysisRequest(text="Requirement text")
    print("  ✓ SemanticAnalysisRequest")
    
    # SemanticAnalysisResponse
    sresp = SemanticAnalysisResponse(
        id="a1",
        text="text",
        entities=[{"name": "User", "type": "actor"}],
        relations=[{"from": "User", "to": "System"}],
        ambiguities=[{"word": "shall", "confidence": 0.8}],
        confidence_score=0.9,
        processed_at=now_str   # was "now"
    )
    print("  ✓ SemanticAnalysisResponse")
    
    # PredictiveAnalysisRequest
    preq = PredictiveAnalysisRequest(text="System must be secure")
    print("  ✓ PredictiveAnalysisRequest")
    
    # PredictiveAnalysisResponse
    presp = PredictiveAnalysisResponse(
        id="p1",
        text="text",
        complexity_score=65,
        estimated_effort_weeks=10.5,
        cost_index="high",
        risk_level="high",
        recommendations=["Use encryption"],
        confidence_score=0.85,
        processed_at=now_str   # was "now"
    )
    print("  ✓ PredictiveAnalysisResponse")
    
    # AnalysisResult
    result = AnalysisResult(
        semantic_analysis=sresp,
        predictive_analysis=presp,
        overall_confidence=0.85,
        generated_at=now_str   # was "now"
    )
    print("  ✓ AnalysisResult")
    
def test_import_all_schemas():
    print("\n📦 Testing all exports...")
    expected = [
        "Token", "TokenData", "UserLogin", "PasswordReset", "PasswordChange",
        "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserInDB",
        "DocumentBase", "DocumentCreate", "DocumentUploadResponse", "DocumentSummary",
        "DocumentDetail", "DocumentDeleteResponse",
        "ValidationRequest", "DocumentValidationRequest", "DefectResponse",
        "ValidationResponse", "DocumentValidationResponse",
        "TraceabilityEntry", "TraceabilityNoteCreate", "TraceabilityNoteResponse",
        "VisualizationRequest", "VisualizationResponse",
        "SemanticAnalysisRequest", "SemanticAnalysisResponse",
        "PredictiveAnalysisRequest", "PredictiveAnalysisResponse", "AnalysisResult"
    ]
    for name in expected:
        assert name in globals(), f"Missing {name}"
    print("  ✓ All exports present")

if __name__ == "__main__":
    print("=" * 60)
    print("VisSpec - Pydantic Schema Test Suite")
    print("=" * 60)
    try:
        test_auth_schemas()
        test_user_schemas()
        test_document_schemas()
        test_validation_schemas()
        test_traceability_schemas()
        test_visualization_schemas()
        test_analysis_schemas()
        test_import_all_schemas()
        print("\n" + "=" * 60)
        print("🎉 All schema tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        sys.exit(1)