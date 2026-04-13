from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Optional

from models.user import User, UserRole
from utils.security import verify_token
from config.database import get_db

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from the JWT token
    This function extracts the token from the Authorization header,
    decodes it, and retrieves the corresponding user from the database.
    Args:
        credentials (HTTPAuthorizationCredentials): Contains the JWT token
        db (Session): Database session
    Returns:
        User: The authenticated user object
    Raises:
        HTTPException: If token is invalid or user doesn't exist
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token to get the payload
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        
        # Extract email from the token payload
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        # Query the database for the user with the extracted email
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        
        return user
    except JWTError:
        raise credentials_exception


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get the current authenticated user and verify they are active
    """
    if current_user.is_active != 1:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_role: UserRole):
    """
    Create a dependency that requires a specific user role
    This function returns a dependency that checks if the current user
    has the required role or is a supervisor (who can access all roles)
    Args:
        required_role (UserRole): The role required to access the resource
    Returns:
        function: A dependency function that validates user role
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # Allow access if user has the required role or is a supervisor
        user_role = current_user.role if isinstance(current_user.role, str) else current_user.role.value
        required = required_role.value
        if user_role != required and user_role != UserRole.SUPERVISOR.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required}"
            )
        return current_user
    return role_checker