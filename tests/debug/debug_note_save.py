#!/usr/bin/env python3
"""Debug script to test note saving functionality."""

import requests
import json

def test_traceability_endpoints():
    """Test traceability endpoints to debug note saving issue."""
    
    base_url = "http://localhost:8000"
    
    print("=== Debugging Traceability Note Saving ===\n")
    
    # Test 1: Get traceability data to see actual structure
    print("1. Testing traceability data retrieval...")
    try:
        # You'll need to replace with an actual project ID
        project_id = "test-project-id"  # Replace with actual project ID
        response = requests.get(f"{base_url}/api/traceability/{project_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Traceability data structure:")
            print(json.dumps(data, indent=2)[:500] + "...")
            
            if data.get('traceability'):
                print(f"\nFound {len(data['traceability'])} requirements")
                if data['traceability']:
                    first_req = data['traceability'][0]
                    print(f"First requirement req_id: {first_req.get('req_id')}")
                    print(f"First requirement keys: {list(first_req.keys())}")
        else:
            print("Error response:", response.text)
            
    except Exception as e:
        print(f"Error getting traceability data: {e}")
    
    # Test 2: Try to save a note
    print("\n2. Testing note saving...")
    try:
        note_data = {
            "req_id": "test-req-id",  # Replace with actual req_id from traceability data
            "content": "Test note content"
        }
        
        response = requests.post(
            f"{base_url}/api/traceability/note",
            json=note_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Save note status: {response.status_code}")
        print(f"Save note response: {response.text}")
        
    except Exception as e:
        print(f"Error saving note: {e}")

if __name__ == "__main__":
    test_traceability_endpoints()
