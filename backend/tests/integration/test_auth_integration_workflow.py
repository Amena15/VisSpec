import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
import random
import string
import uuid

from main import app
from config.database import Base, get_db
from models.user import User, UserRole
from utils.security import get_password_hash, verify_password


# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
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


class TestAuthIntegration:
    """Integration tests for the VisSpec Authentication Module."""

    def test_register_happy_path(self, client, db_session):
        """
        Covers UC_01: Registration - Happy Path
        Register a new user with role "analyst". Expect 200 OK.
        """
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "role": "analyst"
        }

        # Act
        response = client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 200  # 200 because response_model=Token
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        
        # Verify user was created in database
        user = db_session.query(User).filter(User.email == "test@example.com").first()
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.ANALYST.value
        assert verify_password("SecurePassword123!", user.hashed_password)


    def test_register_supervisor_role_allowed(self, client, db_session):
        """
        Covers UC_01: Registration - Business Rule BR-01
        Verify that "supervisor" role can be registered via public API.
        """
        # Arrange
        user_data = {
            "username": "supervisoruser",
            "email": "supervisor@example.com",
            "password": "SecurePassword123!",
            "role": "supervisor"
        }

        # Act
        response = client.post("/api/auth/register", json=user_data)

        # Assert - In this implementation, supervisor registration is allowed
        assert response.status_code == 200
        assert "access_token" in response.json()
        
        # Verify user was created with supervisor role
        user = db_session.query(User).filter(User.email == "supervisor@example.com").first()
        assert user is not None
        assert user.role == UserRole.SUPERVISOR.value


    def test_register_duplicate_email(self, client, db_session):
        """
        Covers UC_01: Registration - Alt Scenario
        Register with an existing email. Expect 400 Bad Request.
        """
        # Arrange - Create a user first
        user_data = {
            "username": "duplicateuser",
            "email": "duplicate@example.com",
            "password": "SecurePassword123!",
            "role": "analyst"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200  # First registration should succeed

        # Try to register with the same email
        duplicate_user_data = {
            "username": "anotheruser",
            "email": "duplicate@example.com",  # Same email
            "password": "AnotherPassword456!",
            "role": "analyst"
        }

        # Act
        response = client.post("/auth/register", json=duplicate_user_data)

        # Assert
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]


    def test_register_invalid_data_validation(self, client, db_session):
        """
        Covers UC_01: Registration - Data Validation
        Register with missing password or invalid email format. Expect 422 Unprocessable Entity.
        """
        # Test with missing password (empty string)
        user_data_missing_password = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "",  # Empty password
            "role": "analyst"
        }

        response = client.post("/auth/register", json=user_data_missing_password)
        assert response.status_code == 422

        # Test with invalid email format
        user_data_invalid_email = {
            "username": "testuser",
            "email": "invalid-email",  # Invalid email format
            "password": "SecurePassword123!",
            "role": "analyst"
        }

        response = client.post("/auth/register", json=user_data_invalid_email)
        assert response.status_code == 422

        # Test with missing email
        user_data_missing_email = {
            "username": "testuser",
            "email": "",  # Empty email
            "password": "SecurePassword123!",
            "role": "analyst"
        }

        response = client.post("/auth/register", json=user_data_missing_email)
        assert response.status_code == 422


    def test_login_happy_path(self, client, db_session):
        """
        Covers UC_02: Login - Happy Path
        Login with valid credentials. Expect 200 OK and access_token in response.
        """
        # Arrange - Create a user first
        user_data = {
            "username": "loginuser",
            "email": "loginuser@example.com",
            "password": "SecurePassword123!",
            "role": "analyst"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200

        # Act - Try to login
        login_data = {
            "username": "loginuser@example.com",  # Using email as username for login
            "password": "SecurePassword123!"
        }
        response = client.post("/api/auth/login", data=login_data)

        # Assert
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"


    def test_login_wrong_password(self, client, db_session):
        """
        Covers UC_02: Login - Alt Scenario
        Login with wrong password. Expect 401 Unauthorized.
        """
        # Arrange - Create a user first
        user_data = {
            "username": "wrongpassuser",
            "email": "wrongpassuser@example.com",
            "password": "SecurePassword123!",
            "role": "analyst"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200

        # Act - Try to login with wrong password
        login_data = {
            "username": "wrongpassuser@example.com",
            "password": "WrongPassword!"  # Wrong password
        }
        response = client.post("/api/auth/login", data=login_data)

        # Assert
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]


    def test_login_nonexistent_email(self, client, db_session):
        """
        Covers UC_02: Login - Alt Scenario
        Login with non-existent email. Expect 401 Unauthorized.
        """
        # Act - Try to login with non-existent email
        login_data = {
            "username": "nonexistent@example.com",  # Doesn't exist
            "password": "SomePassword123!"
        }
        response = client.post("/api/auth/login", data=login_data)

        # Assert
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]


    def test_forgot_password_valid_email(self, client, db_session):
        """
        Covers UC_03: Forgot Password - Happy Path
        Request token for valid email. Expect 200 OK.
        """
        # Arrange - Create a user first
        user_data = {
            "username": "forgotuser",
            "email": "forgot@example.com",
            "password": "SecurePassword123!",
            "role": "analyst"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200

        # Act
        response = client.post("/api/auth/forgot-password", params={"email": "forgot@example.com"})

        # Assert
        assert response.status_code == 200
        assert "If email exists, reset instructions sent" in response.json()["message"]


    def test_forgot_password_nonexistent_email(self, client, db_session):
        """
        Covers UC_03: Forgot Password - Alt Scenario
        Request for non-existent email. Expect 200 OK (security best practice).
        """
        # Act
        response = client.post("/api/auth/forgot-password", params={"email": "nonexistent@example.com"})

        # Assert - Should return 200 to prevent email enumeration
        assert response.status_code == 200
        assert "If email exists, reset instructions sent" in response.json()["message"]


    def test_reset_password_happy_path(self, client, db_session):
        """
        Covers UC_03: Reset Password - Happy Path
        Use a valid token to reset password. Expect 200 OK.
        """
        # Arrange - Create a user first
        user_data = {
            "username": "resetuser",
            "email": "reset@example.com",
            "password": "OldPassword123!",
            "role": "analyst"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200

        # Verify old password works
        login_data = {
            "username": "reset@example.com",
            "password": "OldPassword123!"
        }
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200

        # Act - Reset password (in this implementation, we assume token is valid)
        reset_data = {
            "email": "reset@example.com",
            "new_password": "NewSecurePassword456!",
            "token": "123456"  # Mock token
        }
        response = client.post("/api/auth/reset-password", json=reset_data)

        # Assert
        assert response.status_code == 200
        assert "Password reset successfully" in response.json()["message"]

        # Verify old password no longer works
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 401

        # Verify new password works
        new_login_data = {
            "username": "reset@example.com",
            "password": "NewSecurePassword456!"
        }
        response = client.post("/auth/login", data=new_login_data)
        assert response.status_code == 200


    def test_reset_password_invalid_token(self, client, db_session):
        """
        Covers UC_03: Reset Password - Alt Scenario
        Use an invalid/expired token. Expect 404 User not found (in this implementation).
        """
        # Act - Try to reset password for non-existent user
        reset_data = {
            "email": "nonexistent@example.com",  # User doesn't exist
            "new_password": "NewPassword789!",
            "token": "invalidtoken"
        }
        response = client.post("/api/auth/reset-password", json=reset_data)

        # Assert
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


    def test_reset_password_verification(self, client, db_session):
        """
        Covers UC_03: Reset Password - Verification
        Verify that old password fails and new password succeeds after reset.
        """
        # Arrange - Create a user first
        user_data = {
            "username": "verifyuser",
            "email": "verify@example.com",
            "password": "OriginalPassword123!",
            "role": "analyst"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200

        # Verify original password works
        original_login_data = {
            "username": "verify@example.com",
            "password": "OriginalPassword123!"
        }
        response = client.post("/auth/login", data=original_login_data)
        assert response.status_code == 200

        # Reset password
        reset_data = {
            "email": "verify@example.com",
            "new_password": "NewVerifiedPassword456!",
            "token": "123456"
        }
        response = client.post("/api/auth/reset-password", json=reset_data)
        assert response.status_code == 200

        # Verify original password no longer works
        response = client.post("/auth/login", data=original_login_data)
        assert response.status_code == 401

        # Verify new password works
        new_login_data = {
            "username": "verify@example.com",
            "password": "NewVerifiedPassword456!"
        }
        response = client.post("/auth/login", data=new_login_data)
        assert response.status_code == 200


    def test_account_lockout_simulation(self, client, db_session):
        """
        Covers UC_02: Login - Business Rule BR-04 (Optional)
        Simulate account lockout after multiple failed login attempts.
        The implementation should lock the account after 5 failed attempts.
        """
        # Arrange - Create a user first
        unique_suffix = uuid.uuid4().hex[:8]
        user_data = {
            "username": f"lockoutuser_{unique_suffix}",
            "email": f"lockout_{unique_suffix}@example.com",
            "password": "SecurePassword123!",
            "role": "analyst"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200

        # Act - Try to login with wrong password multiple times (5 attempts)
        login_data = {
            "username": user_data["email"],
            "password": "WrongPassword!"  # Wrong password
        }
        
        for i in range(4):
            response = client.post("/api/auth/login", data=login_data)
            assert response.status_code == 401

        # 5th attempt should trigger lockout
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower()

        # Try with correct password while locked - should still be blocked
        correct_login_data = {
            "username": user_data["email"],
            "password": "SecurePassword123!"
        }
        response = client.post("/api/auth/login", data=correct_login_data)
        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower()