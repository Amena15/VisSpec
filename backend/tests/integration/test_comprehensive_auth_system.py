"""
Comprehensive unit tests for the VisSpec Authentication Module.
Covers all 7 authentication endpoints with happy path and edge case tests.

Endpoints tested:
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/profile
- POST /api/auth/change-password
- POST /api/auth/forgot-password
- POST /api/auth/reset-password
- POST /api/auth/verify-reset-token
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone, timedelta
import uuid

from main import app
from config.database import Base, get_db
from models.user import User, UserRole
from utils.security import verify_password


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def register_user(client, username, email, password, role="analyst"):
    """Helper to register a user and return the response."""
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "role": role,
    }
    return client.post("/api/auth/register", json=user_data)


def login_user(client, email, password):
    """Helper to login and return the response."""
    login_data = {"username": email, "password": password}
    return client.post("/api/auth/login", data=login_data)


def get_auth_header(token):
    """Helper to create authorization header."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------------------------

class TestRegister:
    """Tests for POST /api/auth/register"""

    def test_register_happy_path(self, client, db_session):
        """Register a new analyst user. Expect 200 OK and JWT token."""
        response = register_user(client, "testuser", "test@example.com", "SecurePassword123!")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify user in database
        user = db_session.query(User).filter(User.email == "test@example.com").first()
        assert user is not None
        assert user.username == "testuser"
        assert user.role == UserRole.ANALYST.value
        assert verify_password("SecurePassword123!", user.password_hash)

    def test_register_supervisor_role(self, client, db_session):
        """Register a supervisor user. Expect 200 OK."""
        response = register_user(client, "supervisor1", "supervisor@example.com", "SecurePassword123!", "supervisor")

        assert response.status_code == 200
        user = db_session.query(User).filter(User.email == "supervisor@example.com").first()
        assert user.role == UserRole.SUPERVISOR.value

    def test_register_duplicate_email(self, client):
        """Register with an existing email. Expect 400 Bad Request."""
        register_user(client, "user1", "dup@example.com", "SecurePassword123!")
        response = register_user(client, "user2", "dup@example.com", "AnotherPass456!")

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client):
        """Register with an existing username. Expect 400 Bad Request."""
        register_user(client, "sameuser", "email1@example.com", "SecurePassword123!")
        response = register_user(client, "sameuser", "email2@example.com", "AnotherPass456!")

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_short_password(self, client):
        """Register with password shorter than 8 characters. Expect 422."""
        response = register_user(client, "shortpass", "short@example.com", "Short1!")

        assert response.status_code == 422

    def test_register_password_missing_uppercase(self, client):
        """Register with password missing uppercase. Expect 422."""
        response = register_user(client, "noupper", "noupper@example.com", "password123!")

        assert response.status_code == 422

    def test_register_password_missing_lowercase(self, client):
        """Register with password missing lowercase. Expect 422."""
        response = register_user(client, "nolower", "nolower@example.com", "PASSWORD123!")

        assert response.status_code == 422

    def test_register_password_missing_digit(self, client):
        """Register with password missing digit. Expect 422."""
        response = register_user(client, "nodigit", "nodigit@example.com", "Password!")

        assert response.status_code == 422

    def test_register_password_missing_special(self, client):
        """Register with password missing special character. Expect 422."""
        response = register_user(client, "nospecial", "nospecial@example.com", "Password123")

        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        """Register with invalid email format. Expect 422."""
        response = register_user(client, "bademail", "not-an-email", "SecurePassword123!")

        assert response.status_code == 422

    def test_register_short_username(self, client):
        """Register with username shorter than 3 characters. Expect 422."""
        response = register_user(client, "ab", "shortname@example.com", "SecurePassword123!")

        assert response.status_code == 422

    def test_register_invalid_username_chars(self, client):
        """Register with username containing invalid characters. Expect 422."""
        response = register_user(client, "user@name", "invalidname@example.com", "SecurePassword123!")

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login Tests
# ---------------------------------------------------------------------------

class TestLogin:
    """Tests for POST /api/auth/login"""

    def test_login_happy_path(self, client):
        """Login with valid credentials. Expect 200 OK and JWT token."""
        register_user(client, "loginuser", "login@example.com", "SecurePassword123!")
        response = login_user(client, "login@example.com", "SecurePassword123!")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """Login with wrong password. Expect 401 Unauthorized."""
        register_user(client, "wrongpass", "wrongpass@example.com", "SecurePassword123!")
        response = login_user(client, "wrongpass@example.com", "WrongPassword!")

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_email(self, client):
        """Login with non-existent email. Expect 401 Unauthorized."""
        response = login_user(client, "nonexistent@example.com", "SomePassword123!")

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_account_lockout_after_5_attempts(self, client):
        """Account should lock after 5 failed attempts. Expect 423 after lockout."""
        unique_suffix = uuid.uuid4().hex[:8]
        email = f"lockout_{unique_suffix}@example.com"
        register_user(client, f"lockout_{unique_suffix}", email, "SecurePassword123!")

        # First 4 failed attempts should still be unauthorized
        for _ in range(4):
            response = login_user(client, email, "WrongPassword!")
            assert response.status_code == 401

        # 5th failed attempt should lock the account
        response = login_user(client, email, "WrongPassword!")
        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower()

        # Correct credentials should still be blocked while locked
        response = login_user(client, email, "SecurePassword123!")
        assert response.status_code == 423


# ---------------------------------------------------------------------------
# Profile Tests
# ---------------------------------------------------------------------------

class TestProfile:
    """Tests for GET /api/auth/profile"""

    def test_get_profile_happy_path(self, client):
        """Get profile with valid token. Expect 200 OK and user data."""
        register_response = register_user(client, "profileuser", "profile@example.com", "SecurePassword123!")
        token = register_response.json()["access_token"]

        response = client.get("/api/auth/profile", headers=get_auth_header(token))

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profile@example.com"
        assert data["username"] == "profileuser"
        assert data["role"] == UserRole.ANALYST.value
        assert "user_id" in data
        assert "is_active" in data

    def test_get_profile_unauthorized_no_token(self, client):
        """Get profile without token. Expect 401/403 Unauthorized."""
        response = client.get("/api/auth/profile")

        assert response.status_code in (401, 403)

    def test_get_profile_invalid_token(self, client):
        """Get profile with invalid token. Expect 401 Unauthorized."""
        response = client.get("/api/auth/profile", headers={"Authorization": "Bearer invalid_token"})

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Change Password Tests
# ---------------------------------------------------------------------------

class TestChangePassword:
    """Tests for POST /api/auth/change-password"""

    def test_change_password_happy_path(self, client):
        """Change password with valid current password. Expect 200 OK."""
        register_response = register_user(client, "changepass", "changepass@example.com", "SecurePassword123!")
        token = register_response.json()["access_token"]

        response = client.post(
            "/api/auth/change-password",
            json={"current_password": "SecurePassword123!", "new_password": "NewPassword456!"},
            headers=get_auth_header(token),
        )

        assert response.status_code == 200
        assert "changed successfully" in response.json()["message"].lower()

        # Verify old password no longer works
        old_login = login_user(client, "changepass@example.com", "SecurePassword123!")
        assert old_login.status_code == 401

        # Verify new password works
        new_login = login_user(client, "changepass@example.com", "NewPassword456!")
        assert new_login.status_code == 200

    def test_change_password_wrong_current_password(self, client):
        """Change password with wrong current password. Expect 400 Bad Request."""
        register_response = register_user(client, "wrongcurrent", "wrongcurrent@example.com", "SecurePassword123!")
        token = register_response.json()["access_token"]

        response = client.post(
            "/api/auth/change-password",
            json={"current_password": "WrongPassword!", "new_password": "NewPassword456!"},
            headers=get_auth_header(token),
        )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_too_short(self, client):
        """Change password to a password shorter than 8 characters. Expect 400."""
        register_response = register_user(client, "shortnew", "shortnew@example.com", "SecurePassword123!")
        token = register_response.json()["access_token"]

        response = client.post(
            "/api/auth/change-password",
            json={"current_password": "SecurePassword123!", "new_password": "Short1"},
            headers=get_auth_header(token),
        )

        assert response.status_code == 400
        assert "at least 8 characters" in response.json()["detail"].lower()

    def test_change_password_unauthorized(self, client):
        """Change password without authentication. Expect 401/403."""
        response = client.post(
            "/api/auth/change-password",
            json={"current_password": "OldPass123!", "new_password": "NewPassword456!"},
        )

        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Forgot Password Tests
# ---------------------------------------------------------------------------

class TestForgotPassword:
    """Tests for POST /api/auth/forgot-password"""

    def test_forgot_password_valid_email(self, client, db_session):
        """Request reset token for valid email. Expect 200 OK with reset_token."""
        register_user(client, "forgotuser", "forgot@example.com", "SecurePassword123!")
        response = client.post("/api/auth/forgot-password", params={"email": "forgot@example.com"})

        assert response.status_code == 200
        data = response.json()
        assert "reset_token" in data
        assert data["expires_in_minutes"] == 15
        assert "message" in data

    def test_forgot_password_nonexistent_email(self, client):
        """Request reset token for non-existent email. Expect 200 OK (security best practice)."""
        response = client.post("/api/auth/forgot-password", params={"email": "nonexistent@example.com"})

        assert response.status_code == 200
        # Should return generic message without revealing if email exists
        assert "message" in response.json()


# ---------------------------------------------------------------------------
# Reset Password Tests
# ---------------------------------------------------------------------------

class TestResetPassword:
    """Tests for POST /api/auth/reset-password"""

    def test_reset_password_happy_path(self, client):
        """Reset password with valid token. Expect 200 OK."""
        register_user(client, "resetuser", "reset@example.com", "OldPassword123!")

        # Request reset token
        forgot_response = client.post("/api/auth/forgot-password", params={"email": "reset@example.com"})
        reset_token = forgot_response.json()["reset_token"]

        # Reset password
        response = client.post(
            "/api/auth/reset-password",
            json={"email": "reset@example.com", "new_password": "NewPassword456!", "token": reset_token},
        )

        assert response.status_code == 200
        assert "reset successfully" in response.json()["message"].lower()

        # Verify old password no longer works
        old_login = login_user(client, "reset@example.com", "OldPassword123!")
        assert old_login.status_code == 401

        # Verify new password works
        new_login = login_user(client, "reset@example.com", "NewPassword456!")
        assert new_login.status_code == 200

    def test_reset_password_invalid_token(self, client):
        """Reset password with invalid token. Expect 400 Bad Request."""
        response = client.post(
            "/api/auth/reset-password",
            json={"email": "any@example.com", "new_password": "NewPassword456!", "token": "invalidtoken"},
        )

        assert response.status_code == 400
        assert "invalid or expired" in response.json()["detail"].lower()

    def test_reset_password_email_mismatch(self, client):
        """Reset password with token for different email. Expect 400 Bad Request."""
        register_user(client, "mismatch1", "mismatch1@example.com", "SecurePassword123!")
        register_user(client, "mismatch2", "mismatch2@example.com", "SecurePassword123!")

        # Get token for mismatch1
        forgot_response = client.post("/api/auth/forgot-password", params={"email": "mismatch1@example.com"})
        reset_token = forgot_response.json()["reset_token"]

        # Try to use token with mismatch2 email
        response = client.post(
            "/api/auth/reset-password",
            json={"email": "mismatch2@example.com", "new_password": "NewPassword456!", "token": reset_token},
        )

        assert response.status_code == 400
        assert "does not match" in response.json()["detail"].lower()

    def test_reset_password_expired_token(self, client):
        """Reset password with expired token. Expect 400 Bad Request."""
        register_user(client, "expired", "expired@example.com", "SecurePassword123!")

        # Get token
        forgot_response = client.post("/api/auth/forgot-password", params={"email": "expired@example.com"})
        reset_token = forgot_response.json()["reset_token"]

        # Manually expire the token by manipulating internal store
        from api.auth import _reset_tokens
        _reset_tokens[reset_token]["expires_at"] = datetime.now(timezone.utc) - timedelta(minutes=1)

        response = client.post(
            "/api/auth/reset-password",
            json={"email": "expired@example.com", "new_password": "NewPassword456!", "token": reset_token},
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Verify Reset Token Tests
# ---------------------------------------------------------------------------

class TestVerifyResetToken:
    """Tests for POST /api/auth/verify-reset-token"""

    def test_verify_reset_token_valid(self, client):
        """Verify a valid reset token. Expect 200 OK with valid=True."""
        register_user(client, "verifyuser", "verify@example.com", "SecurePassword123!")

        # Get token
        forgot_response = client.post("/api/auth/forgot-password", params={"email": "verify@example.com"})
        reset_token = forgot_response.json()["reset_token"]

        response = client.post("/api/auth/verify-reset-token", params={"token": reset_token})

        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_verify_reset_token_invalid(self, client):
        """Verify an invalid reset token. Expect 400 Bad Request."""
        response = client.post("/api/auth/verify-reset-token", params={"token": "invalidtoken"})

        assert response.status_code == 400
        assert "invalid or expired" in response.json()["detail"].lower()

    def test_verify_reset_token_expired(self, client):
        """Verify an expired reset token. Expect 400 Bad Request."""
        register_user(client, "verifyexpired", "verifyexpired@example.com", "SecurePassword123!")

        # Get token
        forgot_response = client.post("/api/auth/forgot-password", params={"email": "verifyexpired@example.com"})
        reset_token = forgot_response.json()["reset_token"]

        # Manually expire the token
        from api.auth import _reset_tokens
        _reset_tokens[reset_token]["expires_at"] = datetime.now(timezone.utc) - timedelta(minutes=1)

        response = client.post("/api/auth/verify-reset-token", params={"token": reset_token})

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

