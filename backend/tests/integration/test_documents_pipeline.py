#!/usr/bin/env python3
import requests
import os
import json
import sys

BASE_URL = 'http://localhost:8000'

TEST_DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_documents')

TEST_CASES = [
    ('SRS.txt', 201, 'Valid TXT'),
    ('large_file.pdf', 201, 'Large PDF'),
    ('test.exe', 400, 'Invalid Type'),
    ('Scanned_image.pdf', 422, 'Scanned PDF')
]

s = requests.Session()

def safe_response(resp):
    try:
        body = resp.json()
        return json.dumps(body, indent=2)[:400] + '...' if len(str(body)) > 400 else resp.text
    except:
        return resp.text[:400] + '...'

print('Document Pipeline Integration Test')
print('Server must be running on localhost:8000')
print()

# Use yousef user from DB
USERNAME = 'yousef@visspec.com'
PASSWORD = 'Yousef@2026'

# Login
print('Login:')
login_resp = s.post(BASE_URL + '/api/auth/login', json={
    'username': USERNAME,
    'password': PASSWORD
})
print('Status:', login_resp.status_code)
print('Response:', safe_response(login_resp))
print()
if login_resp.status_code != 200:
    print('Login failed.')
    print('Integration test cannot continue without authentication.')
    sys.exit(1)

token_resp = login_resp.json()
s.headers['Authorization'] = 'Bearer ' + token_resp['access_token']
print('Auth OK')
print()

# Create project
print('Create project:')
proj_resp = s.post(BASE_URL + '/api/projects', json={'name': 'PipelineTest'})
print('Status:', proj_resp.status_code)
print('Response:', safe_response(proj_resp))
print()
if proj_resp.status_code != 201:
    print('Project creation failed.')
    sys.exit(1)

project_id = proj_resp.json()['project_id']
print('Project ID:', project_id)
print()

# Test uploads
passed = 0
for filename, expected_status, description in TEST_CASES:
    filepath = os.path.join(TEST_DOCS_DIR, filename)
    print(f'{description} ({filename}):', end=' ')
    if not os.path.exists(filepath):
        print('FILE NOT FOUND')
        continue
    with open(filepath, 'rb') as f:
        files = {'file': (filename, f)}
        resp = s.post(BASE_URL + f'/api/documents/upload?project_id={project_id}', files=files)
    print(resp.status_code, end=' ')
    if resp.status_code == expected_status:
        print('- PASS')
        passed += 1
    else:
        print(f'- FAIL (expected {expected_status})')
        print('Response:', safe_response(resp))
    print()

print(f'{passed}/4 tests passed')

