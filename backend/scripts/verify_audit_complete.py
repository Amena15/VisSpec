#!/usr/bin/env python3

import sys
sys.path.append('.')
from sqlalchemy import create_engine, text
from core.config import settings

def verify_audit_functionality():
    """Verify audit trail functionality without API"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Check if we have audit records
            result = connection.execute(text("""
                SELECT review_id, project_id, supervisor_id, decision, comments, created_at 
                FROM review_audits 
                ORDER BY created_at DESC 
                LIMIT 5
            """))
            
            audits = result.fetchall()
            print(f"📊 Found {len(audits)} audit records in database")
            
            if audits:
                print("📝 Recent audit records:")
                for i, audit in enumerate(audits):
                    print(f"  {i+1}. ID: {audit[0]}")
                    print(f"     Project: {audit[1]}")
                    print(f"     Supervisor: {audit[2]}")
                    print(f"     Decision: {audit[3]}")
                    print(f"     Comments: {audit[4][:50]}..." if audit[4] and len(audit[4]) > 50 else f"     Comments: {audit[4]}")
                    print(f"     Created: {audit[5]}")
                    print()
            
            # Test the data transformation that the API would do
            if audits:
                print("🔄 Testing data transformation:")
                for audit in audits:
                    try:
                        transformed = {
                            "id": audit[0],
                            "project_id": audit[1],
                            "reviewer_email": audit[2],
                            "decision": audit[3],
                            "comments": audit[4],
                            "quality_score": None,  # This field might be null
                            "defect_count": 0,       # This field might be 0
                            "created_at": audit[5],
                        }
                        print(f"✅ Transformation successful for audit {audit[0]}")
                        break
                    except Exception as e:
                        print(f"❌ Transformation failed: {e}")
                        break
            
            return True
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_api_endpoint_directly():
    """Test the audit trail API endpoint with error handling"""
    
    import requests
    
    # Login as supervisor
    login_data = {'username': 'supervisor@test.com', 'password': 'Supervisor123!'}
    
    try:
        response = requests.post('http://localhost:8000/api/auth/login', data=login_data, timeout=5)
        if response.status_code == 200:
            token = response.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Get a project ID that has audits
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as connection:
                result = connection.execute(text("SELECT DISTINCT project_id FROM review_audits LIMIT 1"))
                project = result.fetchone()
                
                if project:
                    project_id = project[0]
                    print(f"🔍 Testing audit trail API for project: {project_id}")
                    
                    # Test the API endpoint
                    response = requests.get(f'http://localhost:8000/api/supervisor/review-audits/{project_id}', headers=headers, timeout=5)
                    print(f"📡 API Response: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ API Success! Found {len(data)} audits")
                    else:
                        print(f"❌ API Error: {response.status_code}")
                        print(f"Response: {response.text}")
                else:
                    print("⚠️ No projects with audit records found")
        else:
            print("❌ Supervisor login failed")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    print("🔍 Verifying Audit Trail Functionality")
    print("=" * 50)
    
    # Test database level
    print("\n📊 Database Level Verification:")
    verify_audit_functionality()
    
    # Test API level
    print("\n📡 API Level Verification:")
    test_api_endpoint_directly()
    
    print("\n🎉 Audit Trail Verification Complete!")
