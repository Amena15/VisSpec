from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from models.user import User, UserRole
from schemas.user import UserResponse, UserUpdate
from utils.security import get_current_active_user, require_role
from config.database import get_db

from pydantic import BaseModel

class UserSettings(BaseModel):
    email_notifications: Optional[bool] = True
    push_notifications: Optional[bool] = False
    language: Optional[str] = "en"
    timezone: Optional[str] = "UTC"
    dark_mode: Optional[bool] = False

router = APIRouter()

user_settings_store = {}


@router.get("/settings")
def get_user_settings(current_user: User = Depends(get_current_active_user)):
    user_id = current_user.user_id
    if user_id not in user_settings_store:
        return {
            "email_notifications": True,
            "push_notifications": False,
            "language": "en",
            "timezone": "UTC",
            "dark_mode": False
        }
    return user_settings_store[user_id]


@router.put("/settings")
def update_user_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_active_user)
):
    user_id = current_user.user_id
    user_settings_store[user_id] = settings.model_dump()
    return user_settings_store[user_id]


@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(UserRole.SUPERVISOR)),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        UserResponse(
            user_id=u.user_id,
            username=u.username,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role != UserRole.SUPERVISOR.value and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_role(UserRole.SUPERVISOR)),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.role is not None:
        user.role = user_update.role.value

    db.commit()
    db.refresh(user)

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.SUPERVISOR)),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}
