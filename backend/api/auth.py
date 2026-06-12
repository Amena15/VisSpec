"""
Authentication router handling login, registration, profile, password management, and password reset.
All endpoints live under /api/auth.
"""
import random
import hashlib
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from backend.models.user import User, UserRole
from backend.schemas.auth import Token, UserCreate, UserResponse, PasswordReset, PasswordChange
from backend.utils.security import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    verify_password,
    get_password_hash,
)
from backend.config.database import get_db


router = APIRouter(prefix="/api/auth", tags=["authentication"])

ACCESS_TOKEN_EXPIRE_MINUTES = 60

# In-memory token store (replace with Redis/DB in production)
_reset_tokens: dict[str, dict] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _create_token(user: User, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> dict:
    expires = timedelta(minutes=expires_minutes)
    token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=expires,
    )
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# Registration & Login
# ---------------------------------------------------------------------------

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user and return a JWT token."""
    result = await db.execute(
        select(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    now_str = _now_iso()
    password = user_data.password[:72] if len(user_data.password) > 72 else user_data.password

    db_user = User(
        user_id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        role=user_data.role.value if user_data.role else UserRole.ANALYST.value,
        is_active=1,
        created_at=now_str,
        updated_at=now_str,
    )
    db_user.set_password(password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return _create_token(db_user)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Authenticate with email + password and return a JWT token."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_login_at = _now_iso()
    user.failed_login_attempts = 0
    await db.commit()

    return _create_token(user)


# ---------------------------------------------------------------------------
# Profile & Password Change (authenticated)
# ---------------------------------------------------------------------------

@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    body: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the authenticated user's password."""
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long",
        )

    new_password = body.new_password[:72] if len(body.new_password) > 72 else body.new_password
    current_user.set_password(new_password)
    db.commit()

    return {"message": "Password changed successfully"}


# ---------------------------------------------------------------------------
# Password Reset (unauthenticated)
# ---------------------------------------------------------------------------

@router.post("/forgot-password")
async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
    """Generate a password reset token for the given email."""
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return {"message": "If an account exists for this email, a reset link has been sent."}

    token_data = f"{user.email}{time.time()}{random.random()}"
    reset_token = hashlib.sha256(token_data.encode()).hexdigest()

    _reset_tokens[reset_token] = {
        "email": user.email,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
    }

    return {
        "message": "Password reset token generated.",
        "reset_token": reset_token,
        "expires_in_minutes": 15,
    }


@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset, db: AsyncSession = Depends(get_db)):
    """Reset a user's password using a valid reset token."""
    token_info = _reset_tokens.get(reset_data.token)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if datetime.now(timezone.utc) > token_info["expires_at"]:
        del _reset_tokens[reset_data.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    if token_info["email"] != reset_data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email does not match reset token",
        )

    result = await db.execute(select(User).filter(User.email == reset_data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    new_password = reset_data.new_password[:72] if len(reset_data.new_password) > 72 else reset_data.new_password
    user.set_password(new_password)
    user.updated_at = _now_iso()
    await db.commit()

    del _reset_tokens[reset_data.token]

    return {"message": "Password reset successfully"}


@router.post("/verify-reset-token")
def verify_reset_token(token: str):
    """Check whether a password reset token is still valid."""
    token_info = _reset_tokens.get(token)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if datetime.now(timezone.utc) > token_info["expires_at"]:
        del _reset_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    return {"valid": True}
