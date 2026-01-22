"""User and authentication models."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
import uuid


class UserRole(str, Enum):
    """User roles."""
    ADMIN = "admin"
    USER = "user"


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    is_active: bool = True
    role: UserRole = UserRole.USER


class UserCreate(BaseModel):
    """Model for creating a new user."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    """Model for updating a user."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None


class User(UserBase):
    """Full user model with ID."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with hashed password (for storage)."""
    hashed_password: str


class UserResponse(BaseModel):
    """User response model (without password)."""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime]


class Token(BaseModel):
    """JWT Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    username: str
    role: UserRole
    exp: datetime


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(..., min_length=8)

