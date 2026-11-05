"""NFR test fixtures and shared state."""
import os
import pytest
import asyncio

# Set env vars the app reads at import time
os.environ.setdefault("SECRET_KEY", "vispec_secret_key_for_development_purpose_only")
os.environ.setdefault("ALGORITHM", "HS256")

from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.utils.security import create_access_token


@pytest.fixture
def student_token():
    """JWT token for a student-role user."""
    return create_access_token(data={"sub": "test_student", "role": "student"})


@pytest.fixture
def analyst_token():
    """JWT token for an analyst-role user."""
    return create_access_token(data={"sub": "test_analyst", "role": "analyst"})


@pytest.fixture
def supervisor_token():
    """JWT token for a supervisor-role user."""
    return create_access_token(data={"sub": "test_supervisor", "role": "supervisor"})


@pytest.fixture
async def client():
    """Authenticated ASGI test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c