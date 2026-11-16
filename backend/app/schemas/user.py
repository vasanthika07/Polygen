import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

def validate_password_complexity(password: str) -> str:
    """Validates that a password satisfies security complexity criteria."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(password) > 128:
        raise ValueError("Password must not exceed 128 characters")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter (A-Z)")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter (a-z)")
    if not re.search(r"[0-9\W]", password):
        raise ValueError("Password must contain at least one digit (0-9) or special character")
    return password

class UserRegister(BaseModel):
    name: Optional[str] = Field(None, max_length=128, description="Display name of user")
    username: Optional[str] = Field(None, min_length=3, max_length=64, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., max_length=128, description="Password (at least 8 chars with uppercase, lowercase, digit/symbol)")

    @field_validator("password")
    @classmethod
    def check_password_complexity(cls, v: str) -> str:
        return validate_password_complexity(v)

    @field_validator("username")
    @classmethod
    def check_username_validity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not re.match(r"^[a-zA-Z0-9_-]+$", v):
                raise ValueError("Username can only contain alphanumeric characters, underscores, and hyphens")
        return v

class UserLogin(BaseModel):
    username_or_email: str = Field(..., min_length=1, max_length=255, description="Username or email address")
    password: str = Field(..., min_length=1, max_length=128, description="Account password")

    @field_validator("username_or_email")
    @classmethod
    def trim_username_or_email(cls, v: str) -> str:
        return v.strip()

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128, description="Updated display name")
    email: Optional[EmailStr] = Field(None, description="Updated email address")

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Existing account password")
    new_password: str = Field(..., description="New replacement password")

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, v: str) -> str:
        return validate_password_complexity(v)

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10, description="Valid signed JWT refresh token")

class UserResponse(BaseModel):
    id: str
    name: Optional[str] = None
    username: Optional[str] = None
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 7200
    user: UserResponse
