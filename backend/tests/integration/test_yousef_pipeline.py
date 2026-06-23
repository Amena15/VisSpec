import requests
import os
import sys
import pytest

# Skip all tests in this module - requires backend server running
pytestmark = pytest.mark.skip(reason="Requires backend server running on localhost:8000")

BASE_URL = "http://localhost:8000"


def safe_response(resp):
    try:
        return resp.json()
    except:
        return resp.text


def test_yousef_pipeline():
    """Integration test for Yousef's pipeline"""
    s = requests.Session()

    # Login yousef
    print('Login yousef:')
    login_resp = s.post(BASE_URL + "/api/auth/login", data={
        'username': 'yousef@visspec.com',
        'password': 'Yousef@2026'
    })
    print('Status:', login_resp.status_code)
    print('Response:', safe_response(login_resp))
    print()
    assert login_resp.status_code == 200, 'Login failed'

    token = login_resp.json()['access_token']
    s.headers['Authorization'] = f"Bearer {token}"
    print('Auth OK')
    print()

    # Project
    print('Create project:')
    proj = s.post(BASE_URL + "/api/projects", json={'name': 'Pipeline Test'})
    print('Status:', proj.status_code)
    print('Response:', safe_response(proj))
    print()
    assert proj.status_code == 201, 'Project creation failed'

    pid = proj.json()['project_id']
    print('Project ID:', pid)
    print()

    # Uploads
    test_files = ['SRS.txt', 'large.txt']
    print('Testing uploads:')
    passed = 0
    for fn in test_files:
        fp = f"../test_documents/{fn}"
        print(f'Uploading {fn}:', end=' ')
        if os.path.exists(fp):
            with open(fp, 'rb') as f:
                files = {'file': (fn, f)}
                upload_resp = s.post(BASE_URL + f"/api/documents/upload?project_id={pid}", files=files)
                print(upload_resp.status_code, end=' ')
                if upload_resp.status_code == 201:
                    print('- PASS')
                    passed += 1
                else:
                    print(f'- FAIL')
                    print('Response:', safe_response(upload_resp))
        else:
            print('- FILE NOT FOUND')
        print()

    assert passed > 0, 'No files uploaded successfully'
    print('Pipeline test complete.')

