import requests
import os

BASE_URL = "http://localhost:8000"

s = requests.Session()

# Login yousef
login_resp = s.post(BASE_URL + "/api/auth/login", data={
    'username': 'yousef@visspec.com',
    'password': 'Yousef@2026'
})
print('Login:', login.status_code, login.json())
token = login.json()['access_token']
s.headers['Authorization'] = f"Bearer {token}"

# Project
proj = s.post(BASE_URL + "/api/projects", json={'name': 'Pipeline Test'})
print('Project:', proj.status_code, proj.json())
pid = proj.json()['project_id']

# Uploads
files = ['SRS.txt', 'large.txt']
for fn in files:
    fp = f"../test_documents/{fn}"
    if os.path.exists(fp):
        with open(fp, 'rb') as f:
            files = {'file': (fn, f)}

