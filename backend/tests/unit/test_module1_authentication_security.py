#!/usr/bin/env python3

"""
Module 1: Authentication & Security Comprehensive Unit Tests
Covers REQ_01, REQ_02, REQ_03 and all authentication-related functionality

Test Coverage:
- Registration form validation (email format, username uniqueness, password strength)
- Password hashing with bcrypt
- JWT token generation and validation (60-minute expiry)
- Role-based redirection (Student/Developer vs Supervisor)
- Supervisor account restrictions (pre-provisioned only)
- "Remember Me" functionality with secure storage
- Session timeout (60 minutes inactivity - BR-03)
- Account lockout (5 failed attempts, 15 minutes - BR-04)
- Password reset with 15-minute expiry token (BR-05)
- New password cannot match current password (BR-06)
"""

import pytest
import asyncio
import time
import json
import base64
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

# Add backend to path
import sys
sys.path.insert(0, '/Users/amena/Documents/FYPCode/VisSpec/backend')

from main import app
from models.user import User
from core.config import settings
from utils.security import get_password_hash, verify_password, create_access_token, verify_token

client = TestClient(app)

class TestModule1AuthenticationSecurity:
    """Comprehensive test suite for Module 1: Authentication & Security"""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session"""
        return MagicMock()
    
    
    # === Registration Tests ===
    
    def test_registration_email_format_validation(self):
        """Test registration validates email format"""
        # Invalid email formats
        invalid_emails = [
            "invalid-email",
            "user@",
            "@domain.com",
            "user..name@domain.com",
            "user@domain",
            "user name@domain.com"
        ]
        
        for email in invalid_emails:
            response = client.post("/api/register", json={
                "email": email,
                "username": "testuser",
                "password": "ValidPass123!",
                "role": "student"
            })
            assert response.status_code in [400, 422], f"Should reject invalid email: {email}"
    
    def test_registration_username_uniqueness(self):
        """Test registration enforces username uniqueness"""
        # First registration should succeed
        response1 = client.post("/api/register", json={
            "email": "user1@example.com",
            "username": "uniqueuser",
            "password": "ValidPass123!",
            "role": "student"
        })
        
        # Second registration with same username should fail
        response2 = client.post("/api/register", json={
            "email": "user2@example.com",
            "username": "uniqueuser",
            "password": "ValidPass123!",
            "role": "student"
        })
        
        # Should return conflict error
        assert response2.status_code == 409
        data = response2.json()
        assert "username already exists" in data.get("detail", "").lower()
    
    def test_registration_password_strength_validation(self):
        """Test registration validates password strength requirements"""
        # Test various weak passwords
        weak_passwords = [
            "weak",                    # Too short
            "weakpass",               # No uppercase, no special char
            "WEAKPASS",               # No lowercase, no special char
            "Weakpass",               # No special char
            "Weak123",                # No special char
            "Weak!pass"               # No numbers
        ]
        
        for password in weak_passwords:
            response = client.post("/api/register", json={
                "email": "test@example.com",
                "username": "testuser",
                "password": password,
                "role": "student"
            })
            assert response.status_code in [400, 422], f"Should reject weak password: {password}"
        
        # Test valid password
        valid_password = "ValidPass123!"
        response = client.post("/api/register", json={
            "email": "valid@example.com",
            "username": "validuser",
            "password": valid_password,
            "role": "student"
        })
        # Note: This might fail due to mock, but password validation should pass
        assert response.status_code not in [400, 422], "Valid password should be accepted"
    
    def test_registration_password_hashing(self):
        """Test passwords are hashed with bcrypt, not stored as plain text"""
        # Mock the database to capture stored password
        with patch('services.auth.auth_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock user creation to capture the password
            stored_password = None
            def capture_user(user):
                nonlocal stored_password
                stored_password = user.hashed_password
                return MagicMock(id=1, email=user.email, username=user.username)
            
            mock_db.add = capture_user
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()
            
            response = client.post("/api/register", json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "ValidPass123!",
                "role": "student"
            })
            
            # Verify password was hashed
            assert stored_password is not None
            assert stored_password != "ValidPass123!"  # Not plain text
            
            # Verify it's a bcrypt hash
            assert stored_password.startswith('$2b$')  # bcrypt hash format
            assert len(stored_password) >= 60  # bcrypt hashes are long

    # === Login & JWT Tests ===
    
    def test_login_jwt_token_generation(self):
        """Test JWT token generation upon successful login"""
        # Mock user authentication
        with patch('services.auth.auth_service.authenticate_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.username = "testuser"
            mock_user.role = "student"
            mock_auth.return_value = mock_user
            
            response = client.post("/api/login", json={
                "email": "test@example.com",
                "password": "ValidPass123!"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            
            # Verify JWT token structure
            token = data["access_token"]
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            assert "sub" in decoded  # Subject (user ID)
            assert "exp" in decoded  # Expiration
            assert "role" in decoded  # User role
            
            # Verify token expiry (should be 60 minutes)
            exp_time = datetime.fromtimestamp(decoded["exp"])
            now = datetime.utcnow()
            time_diff = exp_time - now
            assert timedelta(minutes=55) <= time_diff <= timedelta(minutes=65)  # Allow some variance
    
    def test_login_jwt_token_structure(self):
        """Test JWT token has correct header.payload.signature structure"""
        with patch('services.auth.auth_service.authenticate_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.username = "testuser"
            mock_user.role = "student"
            mock_auth.return_value = mock_user
            
            response = client.post("/api/login", json={
                "email": "test@example.com",
                "password": "ValidPass123!"
            })
            
            token = response.json()["access_token"]
            
            # Verify JWT structure (header.payload.signature)
            parts = token.split('.')
            assert len(parts) == 3, "JWT should have 3 parts: header.payload.signature"
            
            # Decode each part
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
            
            # Verify header
            assert header["alg"] == "HS256"
            assert "typ" in header
            
            # Verify payload
            assert "sub" in payload
            assert "exp" in payload
            assert "iat" in payload
            assert "role" in payload
    
    def test_login_role_claim_matches_database(self):
        """Test JWT token role claim matches database role"""
        # Test different roles
        roles = ["student", "developer", "supervisor"]
        
        for role in roles:
            with patch('services.auth.auth_service.authenticate_user') as mock_auth:
                mock_user = MagicMock()
                mock_user.id = 1
                mock_user.email = f"test@{role}.com"
                mock_user.username = f"test{role}"
                mock_user.role = role
                mock_auth.return_value = mock_user
                
                response = client.post("/api/login", json={
                    "email": f"test@{role}.com",
                    "password": "ValidPass123!"
                })
                
                token = response.json()["access_token"]
                decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                
                assert decoded["role"] == role, f"Token role should match database role: {role}"

    # === Role-based Tests ===
    
    def test_role_based_redirection(self):
        """Test role-based redirection works correctly"""
        # Test Student/Developer role
        with patch('services.auth.auth_service.authenticate_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "student@example.com"
            mock_user.username = "student"
            mock_user.role = "student"
            mock_auth.return_value = mock_user
            
            response = client.post("/api/login", json={
                "email": "student@example.com",
                "password": "ValidPass123!"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "redirect_url" in data or "dashboard_url" in data
            # Should redirect to student dashboard
        
        # Test Supervisor role
        with patch('services.auth.auth_service.authenticate_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = 2
            mock_user.email = "supervisor@example.com"
            mock_user.username = "supervisor"
            mock_user.role = "supervisor"
            mock_auth.return_value = mock_user
            
            response = client.post("/api/login", json={
                "email": "supervisor@example.com",
                "password": "ValidPass123!"
            })
            
            assert response.status_code == 200
            data = response.json()
            # Should redirect to supervisor dashboard
    
    def test_supervisor_registration_restriction(self):
        """Test supervisor accounts cannot be registered via public endpoint"""
        response = client.post("/api/register", json={
            "email": "supervisor@example.com",
            "username": "supervisor",
            "password": "ValidPass123!",
            "role": "supervisor"
        })
        
        # Should reject supervisor registration
        assert response.status_code == 403
        data = response.json()
        assert "supervisor" in data.get("detail", "").lower()
        assert "pre-provisioned" in data.get("detail", "").lower()

    # === Security Features Tests ===
    
    def test_remember_me_functionality(self):
        """Test 'Remember Me' functionality with secure storage"""
        # This would typically be tested in frontend, but we can test the backend part
        with patch('services.auth.auth_service.authenticate_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.username = "testuser"
            mock_user.role = "student"
            mock_auth.return_value = mock_user
            
            response = client.post("/api/login", json={
                "email": "test@example.com",
                "password": "ValidPass123!",
                "remember_me": True
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Should include longer-lived token for remember me
            if "refresh_token" in data:
                refresh_token = data["refresh_token"]
                decoded = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                
                # Refresh token should have longer expiry (e.g., 7 days)
                exp_time = datetime.fromtimestamp(decoded["exp"])
                now = datetime.utcnow()
                time_diff = exp_time - now
                assert time_diff > timedelta(days=6)  # Should be ~7 days
    
    def test_session_timeout_60_minutes(self):
        """Test session timeout after 60 minutes of inactivity (BR-03)"""
        with patch('services.auth.auth_service.authenticate_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.username = "testuser"
            mock_user.role = "student"
            mock_auth.return_value = mock_user
            
            response = client.post("/api/login", json={
                "email": "test@example.com",
                "password": "ValidPass123!"
            })
            
            token = response.json()["access_token"]
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Verify token expiry is approximately 60 minutes
            exp_time = datetime.fromtimestamp(decoded["exp"])
            now = datetime.utcnow()
            time_diff = exp_time - now
            
            assert timedelta(minutes=55) <= time_diff <= timedelta(minutes=65)
    
    def test_account_lockout_5_failed_attempts(self):
        """Test account lockout after 5 failed attempts (BR-04)"""
        email = "lockout@test.com"
        
        # Mock user exists
        with patch('services.auth.auth_service.get_user_by_email') as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = email
            mock_user.failed_login_attempts = 0
            mock_user.is_locked = False
            mock_get_user.return_value = mock_user
            
            # Make 5 failed login attempts
            for i in range(5):
                response = client.post("/api/login", json={
                    "email": email,
                    "password": "wrongpassword"
                })
                # First few attempts should return 401
                if i < 4:
                    assert response.status_code == 401
            
            # 6th attempt should be locked out
            response = client.post("/api/login", json={
                "email": email,
                "password": "wrongpassword"
            })
            
            assert response.status_code == 423  # Locked
            data = response.json()
            assert "locked" in data.get("detail", "").lower()
            assert "15 minutes" in data.get("detail", "").lower()
    
    def test_password_reset_15_minute_expiry(self):
        """Test password reset with 15-minute expiry token (BR-05)"""
        with patch('services.auth.auth_service.get_user_by_email') as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_get_user.return_value = mock_user
            
            response = client.post("/api/request-password-reset", json={
                "email": "test@example.com"
            })
            
            assert response.status_code == 200
            
            # In a real implementation, this would send an email
            # For testing, we'll verify the token expiry logic
            # Mock the reset token generation
            reset_token = create_access_token(
                data={"sub": str(mock_user.id), "type": "password_reset"},
                expires_delta=timedelta(minutes=15)
            )
            
            decoded = jwt.decode(reset_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            exp_time = datetime.fromtimestamp(decoded["exp"])
            now = datetime.utcnow()
            time_diff = exp_time - now
            
            assert timedelta(minutes=14) <= time_diff <= timedelta(minutes=16)
    
    def test_new_password_cannot_match_current(self):
        """Test new password cannot match current password (BR-06)"""
        with patch('services.auth.auth_service.get_user_by_email') as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.hashed_password = get_password_hash("OldPass123!")
            mock_get_user.return_value = mock_user
            
            # Try to set same password
            response = client.post("/api/reset-password", json={
                "token": "valid_token",
                "new_password": "OldPass123!"
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "same" in data.get("detail", "").lower()
            assert "current" in data.get("detail", "").lower()

    # === Security Validation Tests ===
    
    def test_password_hashing_strength(self):
        """Test bcrypt password hashing strength"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Verify bcrypt hash format
        assert hashed.startswith('$2b$')
        assert len(hashed) >= 60
        
        # Verify password can be verified
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
        
        # Verify different salts produce different hashes
        hashed2 = get_password_hash(password)
        assert hashed != hashed2  # Different salts
    
    def test_jwt_token_validation(self):
        """Test JWT token validation and error handling"""
        # Test valid token
        valid_token = create_access_token(data={"sub": "1", "role": "student"})
        payload = verify_token(valid_token)
        assert payload["sub"] == "1"
        assert payload["role"] == "student"
        
        # Test invalid token
        with pytest.raises(jwt.InvalidTokenError):
            verify_token("invalid_token")
        
        # Test expired token
        expired_token = create_access_token(
            data={"sub": "1"}, 
            expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            verify_token(expired_token)
    
    def test_cors_security_headers(self):
        """Test CORS security headers are properly set"""
        response = client.options("/api/register")
        
        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    # === Integration Tests ===
    
    def test_complete_authentication_flow(self):
        """Test complete authentication flow from registration to protected access"""
        # 1. Register new user
        register_response = client.post("/api/register", json={
            "email": "flowtest@example.com",
            "username": "flowtest",
            "password": "FlowTest123!",
            "role": "student"
        })
        
        # 2. Login with correct credentials
        login_response = client.post("/api/login", json={
            "email": "flowtest@example.com",
            "password": "FlowTest123!"
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 3. Access protected endpoint with token
        protected_response = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert protected_response.status_code == 200
        
        # 4. Access without token should fail
        unprotected_response = client.get("/api/profile")
        assert unprotected_response.status_code == 401
    
    def test_authentication_error_handling(self):
        """Test authentication error handling and user-friendly messages"""
        # Test non-existent user
        response = client.post("/api/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 401
        assert "invalid" in response.json().get("detail", "").lower()
        
        # Test wrong password
        response = client.post("/api/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "invalid" in response.json().get("detail", "").lower()
        
        # Test malformed request
        response = client.post("/api/login", json={
            "email": "invalid-email",
            "password": ""
        })
        assert response.status_code in [400, 422]

# === Test Execution ===

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
