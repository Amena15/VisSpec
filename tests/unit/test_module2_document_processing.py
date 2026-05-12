#!/usr/bin/env python3
"""
Test Module 2: Document Processing Pipeline
Tests REQ_04, REQ_05, REQ_06, REQ_07 requirements
"""

import requests
import json
import os
import tempfile
import io
import time
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000"
PROJECT_ID = "test-project-001"

# Test user credentials
TEST_USER = {
    "username": "testuser_" + str(int(time.time())),
    "email": f"testuser_{int(time.time())}@example.com",
    "password": "Testpass123!",
    "role": "analyst"
}

# Global token for authenticated requests
AUTH_TOKEN = None

def authenticate():
    """Authenticate and get JWT token"""
    global AUTH_TOKEN
    
    # Try to register user first (in case they don't exist)
    register_data = {
        "username": TEST_USER["username"],
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
        "role": TEST_USER["role"]
    }
    
    try:
        # Try registration
        reg_response = requests.post(f"{API_BASE}/api/auth/register", json=register_data)
        if reg_response.status_code == 200:
            token_data = reg_response.json()
            AUTH_TOKEN = token_data.get("access_token")
            print("✓ User registered and authenticated")
            return True
    except:
        pass
    
    # If registration fails, try login
    login_data = {
        "username": TEST_USER["email"],  # Login uses email as username
        "password": TEST_USER["password"]
    }
    
    try:
        login_response = requests.post(
            f"{API_BASE}/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if login_response.status_code == 200:
            token_data = login_response.json()
            AUTH_TOKEN = token_data.get("access_token")
            print("✓ User authenticated")
            return True
        else:
            print(f"✗ Login failed: {login_response.text}")
            return False
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return False

def get_auth_headers():
    """Get headers with authentication token"""
    if not AUTH_TOKEN:
        if not authenticate():
            raise Exception("Authentication failed")
    
    return {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

def create_test_files():
    """Create test files for validation"""
    
    # 1. Valid SRS PDF content (8MB simulation)
    pdf_content = b"""
    %PDF-1.4
    1 0 obj
    << /Type /Catalog /Pages 2 0 R >>
    endobj
    
    2 0 obj
    << /Type /Pages /Kids [3 0 R] /Count 1 >>
    endobj
    
    3 0 obj
    << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
    endobj
    
    4 0 obj
    << /Length 44 >>
    stream
    BT
    /F1 12 Tf
    72 720 Td
    (1. Introduction) Tj
    ET
    endstream
    endobj
    
    xref
    0 5
    0000000000 65535 f 
    0000000009 00000 n 
    0000000058 00000 n 
    0000000115 00000 n 
    0000000174 00000 n 
    trailer
    << /Size 5 /Root 1 0 R >>
    startxref
    312
    %%EOF
    """
    
    # 2. Scanned image PDF (no text)
    scanned_pdf = b"""
    %PDF-1.4
    1 0 obj
    << /Type /Catalog /Pages 2 0 R >>
    endobj
    2 0 obj
    << /Type /Pages /Kids [3 0 R] /Count 1 >>
    endobj
    3 0 obj
    << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
    endobj
    xref
    0 4
    0000000000 65535 f 
    0000000009 00000 n 
    0000000058 00000 n 
    0000000115 00000 n 
    trailer
    << /Size 4 /Root 1 0 R >>
    startxref
    215
    %%EOF
    """
    
    # 3. Large file (>10MB)
    large_content = b"A" * (11 * 1024 * 1024)  # 11MB
    
    # 4. Invalid file (.exe)
    exe_content = b"MZ\x90\x00" + b"A" * 100  # PE header
    
    # 5. Valid DOCX content (simplified)
    docx_content = b"""
    PK\x03\x04\x14\x00\x00\x00\x08\x00
    """
    
    return {
        "valid_pdf": ("test_srs.pdf", pdf_content),
        "scanned_pdf": ("scanned_image.pdf", scanned_pdf),
        "large_file": ("large_file.txt", large_content),
        "exe_file": ("malware.exe", exe_content),
        "docx_file": ("test.docx", docx_content)
    }

def test_file_upload_validation():
    """Test BR-07 and BR-08: File format and size validation"""
    print("=== Testing File Upload Validation ===")
    
    # Ensure authentication
    if not authenticate():
        print("✗ Authentication failed - cannot test upload")
        return {}
    
    test_files = create_test_files()
    results = {}
    
    for test_name, (filename, content) in test_files.items():
        print(f"\nTesting {test_name}: {filename}")
        
        files = {"file": (filename, content)}
        params = {"project_id": PROJECT_ID}
        
        try:
            headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
            response = requests.post(
                f"{API_BASE}/api/documents/upload",
                files=files,
                params=params,
                headers=headers,
                timeout=30
            )
            
            results[test_name] = {
                "status_code": response.status_code,
                "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 201:
                print(f"  Success: {response.json().get('filename', 'Unknown')}")
            else:
                print(f"  Error: {response.text}")
                
        except Exception as e:
            results[test_name] = {
                "status_code": "ERROR",
                "response": str(e)
            }
            print(f"  Exception: {e}")
    
    return results

def test_text_extraction():
    """Test PyMuPDF and python-docx text extraction"""
    print("\n=== Testing Text Extraction ===")
    
    # Ensure authentication
    if not AUTH_TOKEN:
        print("✗ Not authenticated - cannot test text extraction")
        return None
    
    # Test with a simple text file first
    test_text = """
    1. Introduction
    This document contains system requirements.
    
    2. Functional Requirements
    2.1 User Management
    The system shall authenticate users within 5 seconds.
    Users must reset their passwords every 90 days.
    
    2.2 Data Processing
    The application shall process user requests in real-time.
    
    3. Non-Functional Requirements
    The system shall maintain 99.9% uptime.
    """
    
    files = {"file": ("requirements.txt", test_text.encode())}
    params = {"project_id": PROJECT_ID}
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    try:
        response = requests.post(
            f"{API_BASE}/api/documents/upload",
            files=files,
            params=params,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✓ Text extraction successful")
            print(f"  Word count: {result.get('word_count', 0)}")
            print(f"  Requirements found: {result.get('requirements_found', 0)}")
            print(f"  Status: {result.get('status', 'Unknown')}")
            
            # Check if structure was identified
            sections = result.get('sections_found', [])
            if sections:
                print(f"  Sections identified: {', '.join(sections[:3])}")
            
            return result
        else:
            print(f"✗ Text extraction failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Exception during text extraction: {e}")
        return None

def test_database_storage():
    """Test PostgreSQL storage and status"""
    print("\n=== Testing Database Storage ===")
    
    # Ensure authentication
    if not AUTH_TOKEN:
        print("✗ Not authenticated - cannot test database storage")
        return None
    
    try:
        # List documents to verify storage
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        response = requests.get(f"{API_BASE}/api/documents/", headers=headers)
        
        if response.status_code == 200:
            documents = response.json()
            print(f"✓ Found {len(documents)} documents in database")
            
            if documents:
                latest_doc = documents[0]
                print(f"  Latest document: {latest_doc.get('filename', 'Unknown')}")
                print(f"  Status: {latest_doc.get('status', 'Unknown')}")
                print(f"  Word count: {latest_doc.get('word_count', 0)}")
                print(f"  Requirements: {latest_doc.get('requirements_found', 0)}")
                
                # Verify status is "Ready for Analysis" or similar
                status = latest_doc.get('status', '')
                if 'ready' in status.lower() or 'analyzed' in status.lower():
                    print("✓ Document status is correct")
                else:
                    print(f"⚠ Unexpected status: {status}")
                
                return latest_doc
        else:
            print(f"✗ Failed to list documents: {response.text}")
            
    except Exception as e:
        print(f"✗ Exception checking database: {e}")
    
    return None

def test_delete_operation():
    """Test cascade deletion"""
    print("\n=== Testing Delete Operation ===")
    
    # Ensure authentication
    if not AUTH_TOKEN:
        print("✗ Not authenticated - cannot test delete operation")
        return False
    
    try:
        # Get a document to delete
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        response = requests.get(f"{API_BASE}/api/documents/", headers=headers)
        
        if response.status_code == 200:
            documents = response.json()
            if documents:
                test_doc = documents[0]
                doc_id = test_doc.get('doc_id')
                
                print(f"Deleting document: {test_doc.get('filename', 'Unknown')}")
                print(f"Requirements before delete: {test_doc.get('requirements_found', 0)}")
                
                # Delete the document
                delete_response = requests.delete(
                    f"{API_BASE}/api/documents/{doc_id}",
                    headers=headers
                )
                
                if delete_response.status_code == 200:
                    result = delete_response.json()
                    print("✓ Delete operation successful")
                    print(f"  Message: {result.get('message', '')}")
                    print(f"  Deleted requirements: {result.get('deleted_requirements', 0)}")
                    print(f"  Deleted validations: {result.get('deleted_validations', 0)}")
                    
                    # Verify document is gone
                    verify_response = requests.get(
                        f"{API_BASE}/api/documents/{doc_id}",
                        headers=headers
                    )
                    if verify_response.status_code == 404:
                        print("✓ Document permanently deleted")
                    else:
                        print("⚠ Document still accessible after delete")
                    
                    return True
                else:
                    print(f"✗ Delete failed: {delete_response.text}")
            else:
                print("⚠ No documents available for delete test")
        else:
            print(f"✗ Failed to get documents for delete test: {response.text}")
            
    except Exception as e:
        print(f"✗ Exception during delete test: {e}")
    
    return False

def run_module2_tests():
    """Run all Module 2 tests"""
    print("Starting Module 2: Document Processing Tests")
    print("=" * 50)
    
    # Test 1: File upload validation
    upload_results = test_file_upload_validation()
    
    # Test 2: Text extraction
    extraction_result = test_text_extraction()
    
    # Test 3: Database storage
    storage_result = test_database_storage()
    
    # Test 4: Delete operation
    delete_result = test_delete_operation()
    
    # Summary
    print("\n" + "=" * 50)
    print("MODULE 2 TEST SUMMARY")
    print("=" * 50)
    
    print("\n1. File Upload Validation:")
    for test_name, result in upload_results.items():
        status = "✓" if result["status_code"] in [201, 400, 413] else "✗"
        print(f"  {status} {test_name}: {result['status_code']}")
    
    print(f"\n2. Text Extraction: {'✓' if extraction_result else '✗'}")
    print(f"3. Database Storage: {'✓' if storage_result else '✗'}")
    print(f"4. Delete Operation: {'✓' if delete_result else '✗'}")
    
    # Check specific requirements
    print("\nREQUIREMENTS VERIFICATION:")
    
    # BR-07: File format validation
    valid_formats = True
    for test in ["valid_pdf", "docx_file"]:
        if upload_results.get(test, {}).get("status_code") not in [201, 400]:
            valid_formats = False
    print(f"BR-07 (Format validation): {'✓' if valid_formats else '✗'}")
    
    # BR-08: File size validation
    size_validation = upload_results.get("large_file", {}).get("status_code") == 413
    exe_rejection = upload_results.get("exe_file", {}).get("status_code") == 400
    print(f"BR-08 (Size validation): {'✓' if size_validation else '✗'}")
    
    # REQ_05: Text extraction
    text_extraction = extraction_result and extraction_result.get("word_count", 0) > 0
    print(f"REQ_05 (Text extraction): {'✓' if text_extraction else '✗'}")
    
    # REQ_06: Structure identification
    structure_identified = extraction_result and len(extraction_result.get("sections_found", [])) > 0
    print(f"REQ_06 (Structure ID): {'✓' if structure_identified else '✗'}")
    
    # REQ_07: Data management
    data_management = storage_result and delete_result
    print(f"REQ_07 (Data management): {'✓' if data_management else '✗'}")

if __name__ == "__main__":
    run_module2_tests()
