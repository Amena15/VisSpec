"""Simple test for traceability functionality."""
import requests
import json

def test_traceability_api():
    """Test traceability API endpoints directly."""
    base_url = "http://localhost:8000"
    
    # Test 1: Get traceability data
    print("Testing traceability API...")
    
    try:
        # Get projects first to get a valid project ID
        projects_response = requests.get(f"{base_url}/api/projects", 
                                     headers={"Authorization": "Bearer test-token"})
        
        if projects_response.status_code == 200:
            projects = projects_response.json()
            if projects:
                project_id = projects[0]["project_id"]
                print(f"✅ Found project: {project_id}")
                
                # Test 2: Get traceability data
                trace_response = requests.get(f"{base_url}/api/traceability/{project_id}",
                                           headers={"Authorization": "Bearer test-token"})
                
                if trace_response.status_code == 200:
                    trace_data = trace_response.json()
                    print(f"✅ Traceability data loaded: {len(trace_data.get('traceability', []))} requirements")
                    
                    # Test 3: Save note
                    if trace_data.get('traceability'):
                        req_id = trace_data['traceability'][0]['req_id']
                        note_data = {
                            "req_id": req_id,
                            "content": "Test note from simple test"
                        }
                        
                        save_response = requests.post(f"{base_url}/api/traceability/note",
                                                     json=note_data,
                                                     headers={"Authorization": "Bearer test-token"})
                        
                        if save_response.status_code == 200:
                            print(f"✅ Note saved successfully: {save_response.json()}")
                        else:
                            print(f"❌ Failed to save note: {save_response.status_code} - {save_response.text}")
                    else:
                        print("❌ No traceability data available")
                else:
                    print(f"❌ Failed to get traceability data: {trace_response.status_code}")
            else:
                print(f"❌ Failed to get projects: {projects_response.status_code}")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_traceability_api()
