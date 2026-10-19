"""One-shot provider probe (not part of the evaluation).

Checks, for the configured Groq profile:
  1. the key can list models and gpt-oss-120b is served,
  2. whether the API accepts reasoning_effort="low",
  3. the exact model id the API reports back,
  4. that a real prompt returns parsed JSON with content present.
The API key is read from config and NEVER printed.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import requests

from backend.core.config import settings

KEY = settings.LLM_API_KEY
BASE = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

print("key present:", bool(KEY), "len:", len(KEY))

r = requests.get(f"{BASE}/models", headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
print("models endpoint:", r.status_code)
ids = [m["id"] for m in r.json().get("data", [])] if r.status_code == 200 else []
print("gpt-oss-120b in list:", MODEL in ids)

PROMPT = (
    "You are a strict data extraction API. Output ONLY valid JSON, no markdown.\n"
    "Analyze this requirement and return "
    '{"defects": [{"type", "severity", "confidence", "description", "evidence", "suggestion"}]}.\n'
    "Requirement: The system shall be fast and user-friendly."
)

for effort in ("low", None):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0.1,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }
    if effort:
        payload["reasoning_effort"] = effort
    t0 = time.time()
    r = requests.post(
        f"{BASE}/chat/completions",
        headers={"Authorization": f"Bearer {KEY}"},
        json=payload,
        timeout=120,
    )
    label = f"reasoning_effort={effort}" if effort else "no reasoning_effort"
    print(f"--- {label}: HTTP {r.status_code} ({time.time() - t0:.1f}s)")
    if r.status_code == 200:
        d = r.json()
        msg = d["choices"][0]["message"]
        content = msg.get("content") or ""
        print("model returned:", d.get("model"))
        print("finish_reason:", d["choices"][0].get("finish_reason"))
        print("content empty:", not content.strip())
        try:
            parsed = json.loads(content)
            print("json parsed:", True, "| n_defects:", len(parsed.get("defects", [])))
        except Exception as e:
            print("json parsed:", False, "|", str(e)[:80])
            print("content head:", content[:200])
    else:
        print("error body:", r.text[:300])
