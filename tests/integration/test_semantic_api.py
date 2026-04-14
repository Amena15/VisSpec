#!/usr/bin/env python3
"""Test script for semantic analysis endpoint"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# First, we need to get a token - check if we can register/login
def get_auth_token():
    """Try to get an auth token by registering and logging in"""
    # Try to register a test user
    register_data = {
        "username": "test_semantic_user",
        "email": "test_semantic@example.com",
        "password": "TestPass123!@#",
    }
    
    try:
        # Register
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        print(f"Register response: {reg_resp.status_code}")
        
        if reg_resp.status_code == 200:
            token = reg_resp.json().get("access_token")
            print(f"Registration successful, got token")
            return token
        
        # If user already exists, try login
        if reg_resp.status_code == 400:
            print("User already exists, trying login...")
        
        # Login using OAuth2PasswordRequestForm (form data, not JSON)
        login_data = {
            "username": "test_semantic@example.com",  # OAuth2 uses 'username' field for email
            "password": "TestPass123!@#"
        }
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            data=login_data,  # Form data, not JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Login response: {login_resp.status_code}")
        
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            return token
        else:
            print(f"Login failed: {login_resp.text[:200]}")
    except Exception as e:
        print(f"Auth error: {e}")
    
    return None

def test_semantic_analysis(token, test_case):
    """Test a single semantic analysis request"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"text": test_case["text"]}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analysis/semantic",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {
            "status_code": 0,
            "error": str(e)
        }

def main():
    test_cases = [
        {
            "name": "Well-Written Security Requirement",
            "text": "The system shall lock user accounts after 5 failed login attempts within 15 minutes. The system must notify users via email after account lockout. Passwords shall be hashed using Argon2."
        },
        {
            "name": "Poorly-Written Requirement",
            "text": "The system should be fast and user-friendly. It may have good security. Data retention should be appropriate. The system must comply with relevant regulations."
        },
        {
            "name": "Healthcare Domain",
            "text": "The electronic health record system shall maintain patient data confidentiality. Only authorized medical staff can access patient records. Data retention period should be appropriate. System must comply with relevant privacy regulations."
        },
        {
            "name": "Banking Domain",
            "text": "The banking system must authenticate users using multi-factor authentication. Transaction amounts exceeding $10,000 require supervisor approval within 2 business days. All transactions must be logged with timestamps and user IP addresses."
        },
        {
            "name": "E-Commerce Domain",
            "text": "Customers can add items to shopping cart. The system usually processes payments quickly. Orders may be cancelled before shipping. Refunds are sometimes issued for defective products."
        },
        {
            "name": "Safety-Critical System",
            "text": "The braking system shall engage within 50 milliseconds when obstacle detected at 10 meters. The system must sound an alarm immediately. Brake pressure must reach 100% within 100 milliseconds."
        },
        {
            "name": "API Requirements",
            "text": "The REST API must support GET, POST, PUT, and DELETE methods. Endpoints shall return JSON responses. The system should handle many concurrent requests. Error messages must be descriptive."
        },
        {
            "name": "Mixed Quality",
            "text": "REQ-001: The system shall allow users to reset passwords via email. REQ-002: Password reset links must expire after a reasonable time. REQ-003: The system should log all password reset attempts."
        },
        {
            "name": "Performance Requirements",
            "text": "The web server must handle high traffic loads. Page load time should be fast. Database queries must be optimized. The system should scale to support future growth."
        },
        {
            "name": "IEEE 830 Style SRS Fragment",
            "text": "3.1 Functional Requirements: The system shall provide user authentication via email and password. 3.2 Security: Passwords must be stored using Argon2 hashing. Accounts shall lock after 5 failed attempts. 3.3 Performance: System response time shall be less than 200ms for 95% of requests."
        }
    ]
    
    # Get auth token
    print("=" * 80)
    print("GETTING AUTH TOKEN")
    print("=" * 80)
    token = get_auth_token()
    
    if not token:
        print("\n❌ Failed to get auth token. Trying without authentication...")
        # Try without auth to see what happens
        headers = {}
        payload = {"text": "Test"}
        try:
            resp = requests.post(f"{BASE_URL}/api/analysis/semantic", headers=headers, json=payload)
            print(f"Unauthenticated response: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")
        return
    
    print(f"\n✓ Got token: {token[:50]}...\n")
    
    # Run tests
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print("=" * 80)
        print(f"TEST {i}/{len(test_cases)}: {test_case['name']}")
        print("=" * 80)
        print(f"Input: {test_case['text'][:100]}...")
        
        result = test_semantic_analysis(token, test_case)
        results.append({
            "name": test_case["name"],
            "input": test_case["text"],
            "result": result
        })
        
        if result["status_code"] == 200:
            response = result["response"]
            print(f"\n✓ Success!")
            print(f"  Method: {response.get('method', 'N/A')}")
            print(f"  Confidence: {response.get('confidence_score', 0):.2f}")
            print(f"  Entities: {len(response.get('entities', []))}")
            print(f"  Relations: {len(response.get('relations', []))}")
            print(f"  Ambiguities: {len(response.get('ambiguities', []))}")
            
            # Show first few entities
            if response.get('entities'):
                print(f"\n  Sample entities:")
                for ent in response['entities'][:3]:
                    print(f"    - [{ent.get('label', '?')}] {ent.get('text', 'N/A')}")
            
            # Show ambiguities if any
            if response.get('ambiguities'):
                print(f"\n  Ambiguities found:")
                for amb in response['ambiguities'][:3]:
                    print(f"    - [{amb.get('severity', '?')}] '{amb.get('term', 'N/A')}': {amb.get('description', '')[:80]}")
        else:
            print(f"\n❌ Failed with status {result['status_code']}")
            print(f"  Error: {result.get('response', result.get('error', 'Unknown'))[:200]}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    success_count = sum(1 for r in results if r["result"]["status_code"] == 200)
    print(f"\nSuccessful: {success_count}/{len(results)}")
    
    if success_count > 0:
        print("\nConfidence Scores:")
        for r in results:
            if r["result"]["status_code"] == 200:
                resp = r["result"]["response"]
                conf = resp.get('confidence_score', 0)
                method = resp.get('method', 'N/A')
                amb_count = len(resp.get('ambiguities', []))
                print(f"  {r['name']}: {conf:.2f} (method: {method}, ambiguities: {amb_count})")
    
    # Save full results
    output_file = "semantic_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✓ Full results saved to {output_file}")

if __name__ == "__main__":
    main()
