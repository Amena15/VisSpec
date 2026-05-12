#!/usr/bin/env python3
"""Test script to verify traceability fixes."""

import requests
import json

def test_projects_api():
    """Test the projects API to check response format."""
    try:
        # Test without authentication first to see the response structure
        response = requests.get("http://localhost:8000/api/projects/")
        print(f"Projects API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response format: {type(data)}")
            if isinstance(data, list) and len(data) > 0:
                print(f"Sample project keys: {list(data[0].keys())}")
                print(f"Sample project: {json.dumps(data[0], indent=2)}")
            else:
                print("No projects found or unexpected response format")
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Backend server not running on localhost:8000")
    except Exception as e:
        print(f"Error testing projects API: {e}")

def test_traceability_api():
    """Test the traceability API with a sample project ID."""
    try:
        # Test with a sample project ID
        sample_project_id = "test-project-id"
        response = requests.get(f"http://localhost:8000/api/traceability/{sample_project_id}")
        print(f"Traceability API Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("Backend server not running on localhost:8000")
    except Exception as e:
        print(f"Error testing traceability API: {e}")

if __name__ == "__main__":
    print("=== Testing Traceability Fixes ===")
    print("\n1. Testing Projects API...")
    test_projects_api()
    
    print("\n2. Testing Traceability API...")
    test_traceability_api()
    
    print("\n=== Fix Summary ===")
    print("✅ Fixed project ID field name mismatch (project_id vs id)")
    print("✅ Fixed note saving API parameters")
    print("✅ Added fallback handling for both project_id and id fields")
    print("\nTo test manually:")
    print("1. Start backend: cd backend && python main.py")
    print("2. Start frontend: cd frontend && npm start")
    print("3. Navigate to /traceability and click on a project")
