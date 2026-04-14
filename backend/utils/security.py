from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config.database import get_db
from core.config import settings
from models.user import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")  # Changed to email since we store email as subject
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = verify_token(token)
    email = payload.get("sub")  # This is the email stored in the token

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()  # Changed to filter by email

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.is_active != 1:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate a user by email and password
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    # Check if account is locked
    if user.locked_until:
        from datetime import datetime, timezone
        lock_until = datetime.fromisoformat(user.locked_until)
        if datetime.now(timezone.utc) < lock_until:
            return None
        # Lock expired, reset attempts
        user.failed_login_attempts = 0
        user.locked_until = None
    # Verify password
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            from datetime import datetime, timezone, timedelta
            user.locked_until = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        db.commit()
        return None
    return user


def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        user_role = current_user.role if isinstance(current_user.role, str) else current_user.role.value
        required = required_role.value
        if user_role != required and user_role != UserRole.SUPERVISOR.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required}"
            )
        return current_user
    return role_checker