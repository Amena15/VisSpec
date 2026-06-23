# test_groq.py
import requests
import os
import sys

# Try to load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

print(f"--- Groq API Diagnostic ---")
print(f"API Key found: {'Yes (' + api_key[:10] + '...)' if api_key else 'NO (Empty or missing)'}")
print(f"Model requested: {model}")

if not api_key:
    print("ERROR: GROQ_API_KEY is empty. Please set it in your .env file.")
    sys.exit(1)

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": model,
    "messages": [{"role": "user", "content": "Say hello."}],
    "temperature": 0.1,
    "max_tokens": 10
}

print("Sending test request to Groq...")
try:
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS! The API key and model are valid.")
        print(f"Response: {response.json()['choices'][0]['message']['content']}")
    else:
        print("FAILED! Here is the exact error from Groq:")
        try:
            print(response.json())
        except Exception:
            print(response.text)
except Exception as e:
    print(f"Request failed: {e}")