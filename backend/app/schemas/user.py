from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    name: Optional[str] = Field(None, max_length=128, description="Display name of user")
    username: Optional[str] = Field(None, max_length=64, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")

class UserLogin(BaseModel):
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="User password")

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
    token_type: str = "bearer"
    user: UserResponse
