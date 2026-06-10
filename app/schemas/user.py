"""Pydantic schemas for user input and output."""
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.user import UserRole


class UserCreate(BaseModel):
    """Input shape when an admin creates a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.READER


class UserResponse(BaseModel):
    """Output shape when returning user info — NEVER includes the password."""
    id: int
    username: str
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Input shape for the login endpoint."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Output shape after successful login — contains the JWT."""
    access_token: str
    token_type: str = "bearer"