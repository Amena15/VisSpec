from pydantic import BaseModel
from typing import Optional
from backend.models.user import UserRole


class UserBase(BaseModel):
    username: str
    email: str
    role: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    is_active: int
    created_at: str

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    password_hash: str