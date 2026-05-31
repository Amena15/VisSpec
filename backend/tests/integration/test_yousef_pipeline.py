import requests
import os
import sys

BASE_URL = "http://localhost:8000"

s = requests.Session()

def safe_response(resp):
    try:
        return resp.json()
    except:
        return resp.text

# Login yousef
print('Login yousef:')
login_resp = s.post(BASE_URL + "/api/auth/login", data={
    'username': 'yousef@visspec.com',
    'password': 'Yousef@2026'
})
print('Status:', login_resp.status_code)
print('Response:', safe_response(login_resp))
print()

if login_resp.status_code != 200:
    print('Login failed.')
    sys.exit(1)

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

if proj.status_code != 201:
    print('Project creation failed.')
    sys.exit(1)

pid = proj.json()['project_id']
print('Project ID:', pid)
print()

# Uploads
files = ['SRS.txt', 'large.txt']
print('Testing uploads:')
for fn in files:
    fp = f"../test_documents/{fn}"
    print(f'Uploading {fn}:', end=' ')
    if os.path.exists(fp):
        with open(fp, 'rb') as f:
            files = {'file': (fn, f)}
            upload_resp = s.post(BASE_URL + f"/api/documents/upload?project_id={pid}", files=files)
            print(upload_resp.status_code, end=' ')
            if upload_resp.status_code == 201:
                print('- PASS')
            else:
                print(f'- FAIL')
                print('Response:', safe_response(upload_resp))
    else:
        print('- FILE NOT FOUND')
    print()

print('Pipeline test complete.')

