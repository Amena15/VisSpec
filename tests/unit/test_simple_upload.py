#!/usr/bin/env python3
import requests
import time

# Create new user
username = f"testuser_{int(time.time())}"
email = f"{username}@example.com"
password = "Testpass123!"

print("Creating user...")
reg_response = requests.post("http://localhost:8000/api/auth/register", json={
    "username": username,
    "email": email,
    "password": password,
    "role": "analyst"
})

if reg_response.status_code == 200:
    token = reg_response.json().get("access_token")
    print("✓ User created and authenticated")
    
    # Test upload with valid text file
    with open("test_valid_srs.txt", "rb") as f:
        files = {"file": ("requirements.txt", f.read())}
        headers = {"Authorization": f"Bearer {token}"}
        
        print("Uploading document...")
        upload_response = requests.post(
            "http://localhost:8000/api/documents/upload?project_id=test-project",
            files=files,
            headers=headers
        )
        
        print(f"Upload status: {upload_response.status_code}")
        if upload_response.status_code == 201:
            result = upload_response.json()
            print(f"✓ Document uploaded successfully")
            print(f"  Filename: {result.get('filename')}")
            print(f"  Word count: {result.get('word_count')}")
            print(f"  Requirements found: {result.get('requirements_found')}")
            print(f"  Status: {result.get('status')}")
            print(f"  Sections: {result.get('sections_found', [])}")
        else:
            print(f"✗ Upload failed: {upload_response.text}")
else:
    print(f"✗ Registration failed: {reg_response.text}")
