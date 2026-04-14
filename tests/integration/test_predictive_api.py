#!/usr/bin/env python3
"""Test script for predictive analysis endpoint"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# First, we need to get a token - check if we can register/login
def get_auth_token():
    """Try to get an auth token by registering and logging in"""
    # Try to register a test user
    register_data = {
        "username": "test_predictive_user",
        "email": "test_predictive@example.com",
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
            "username": "test_predictive@example.com",  # OAuth2 uses 'username' field for email
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

def test_predictive_analysis(token, test_case):
    """Test a single predictive analysis request"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"text": test_case["text"]}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analysis/predictive",
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
            "name": "Simple Feature",
            "text": "The system shall display a welcome message to users after login."
        },
        {
            "name": "CRUD Operations",
            "text": "Users can create, read, update, and delete their personal profile information. The system shall validate email format before saving. Profile changes must be logged with timestamps."
        },
        {
            "name": "E-Commerce Checkout",
            "text": "The e-commerce system must calculate shipping costs based on user location, package weight, and selected shipping speed. The system shall apply discounts for orders over $50. Users can apply one promo code per order. Payment processing shall be handled by Stripe API."
        },
        {
            "name": "Banking Transfer",
            "text": "The banking system shall process international wire transfers. The system must validate recipient bank details against SWIFT database. If validation fails, the system shall notify the user and log the attempt. For transfers exceeding $10,000, the system requires two-factor authentication and supervisor approval."
        },
        {
            "name": "Healthcare Compliance",
            "text": "The healthcare system must maintain patient records with full audit trail. The system shall support role-based access (doctor, nurse, admin, patient). Patient data must be encrypted at rest and in transit. The system must comply with HIPAA and GDPR regulations. Data retention period is 7 years. Real-time synchronization required across 3 regional data centers."
        },
        {
            "name": "Vague Requirement",
            "text": "The system should be fast and reliable. It may have a user-friendly interface. The software must handle many users. Security features must be adequate."
        },
        {
            "name": "Integration API",
            "text": "The system shall integrate with external payment gateway (Stripe API). It must handle webhook callbacks for payment success/failure. The system shall retry failed callbacks up to 3 times with exponential backoff. Payment failures must be logged with timestamps and error codes."
        },
        {
            "name": "Security Authentication",
            "text": "The authentication system must implement multi-factor authentication using SMS or authenticator app. Passwords must be hashed using Argon2. Accounts lock after 5 failed attempts for 15 minutes. JWT tokens expire after 60 minutes. Session timeout after 30 minutes of inactivity."
        },
        {
            "name": "Real-Time Performance",
            "text": "The system must respond to user requests within 200 milliseconds at 95th percentile under 1000 concurrent users. Real-time notifications must be delivered within 5 seconds. The system must handle 10,000 transactions per second during peak hours. Database queries must complete within 50ms."
        },
        {
            "name": "Enterprise-Grade",
            "text": "The system must support multi-tenancy with complete data isolation between 500+ organizations. Real-time synchronization required across 5 regional data centers. 99.999% uptime required. Disaster recovery RPO = 15 minutes, RTO = 1 hour. Must support 1 million concurrent users. GDPR and CCPA compliance required."
        }
    ]
    
    # Get auth token
    print("=" * 80)
    print("GETTING AUTH TOKEN")
    print("=" * 80)
    token = get_auth_token()
    
    if not token:
        print("\n❌ Failed to get auth token. Exiting...")
        return
    
    print(f"\n✓ Got token: {token[:50]}...\n")
    
    # Run tests
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print("=" * 80)
        print(f"TEST {i}/{len(test_cases)}: {test_case['name']}")
        print("=" * 80)
        print(f"Input: {test_case['text'][:100]}...")
        
        result = test_predictive_analysis(token, test_case)
        results.append({
            "name": test_case["name"],
            "input": test_case["text"],
            "result": result
        })
        
        if result["status_code"] == 200:
            response = result["response"]
            print(f"\n✓ Success!")
            print(f"  Complexity Score: {response.get('complexity_score', 0)}")
            print(f"  Estimated Effort: {response.get('estimated_effort_weeks', 0):.1f} weeks")
            print(f"  Cost Index: {response.get('cost_index', 'N/A')}")
            print(f"  Risk Level: {response.get('risk_level', 'N/A')}")
            print(f"  Confidence: {response.get('confidence_score', 0):.2f}")
            print(f"  Recommendations: {len(response.get('recommendations', []))}")
            
            # Show complexity breakdown if available
            if response.get('complexity_breakdown'):
                breakdown = response['complexity_breakdown']
                print(f"\n  Breakdown:")
                print(f"    Actors: {breakdown.get('actor_count', 0)}")
                print(f"    Requirements: {breakdown.get('requirement_count', 0)}")
                print(f"    Modal Density: {breakdown.get('modal_density', 0)}")
                print(f"    Vague Density: {breakdown.get('vague_density', 0)}")
                print(f"    Interaction Depth: {breakdown.get('interaction_depth', 0)}")
            
            # Show recommendations
            if response.get('recommendations'):
                print(f"\n  Recommendations:")
                for rec in response['recommendations'][:5]:
                    print(f"    - {rec[:100]}")
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
        print("\nComplexity & Effort Analysis:")
        for r in results:
            if r["result"]["status_code"] == 200:
                resp = r["result"]["response"]
                complexity = resp.get('complexity_score', 0)
                weeks = resp.get('estimated_effort_weeks', 0)
                cost = resp.get('cost_index', 'N/A')
                risk = resp.get('risk_level', 'N/A')
                confidence = resp.get('confidence_score', 0)
                print(f"  {r['name']}")
                print(f"    Complexity: {complexity} | Weeks: {weeks:.1f} | Cost: {cost} | Risk: {risk} | Confidence: {confidence:.2f}")
    
    # Save full results
    output_file = "predictive_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✓ Full results saved to {output_file}")

if __name__ == "__main__":
    main()
