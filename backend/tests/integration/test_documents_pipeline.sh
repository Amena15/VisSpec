#!/bin/zsh
set -e

BASE_URL="http://localhost:8000"

# 1. Register
curl -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "pipeline_test2", "password": "SecurePass123!", "role": "developer"}'

echo "Register done"

# 2. Login get token
TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":
