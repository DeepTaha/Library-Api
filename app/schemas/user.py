"""Pydantic schemas for user input and output."""
from datetime import datetime, date
from pydantic import BaseModel, Field
from app.models.user import UserRole


class UserCreate(BaseModel):
    """Input shape when an admin creates a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.READER
    email: str | None = None
    date_of_birth: date | None = None


class UserResponse(BaseModel):
    """Output shape when returning user info — NEVER includes the password."""
    id: int
    username: str
    role: UserRole
    email: str | None
    date_of_birth: date | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Input shape for PATCH /users/{id} — all fields optional."""
    username: str | None = Field(None, min_length=3, max_length=50)
    role: UserRole | None = None
    email: str | None = None
    date_of_birth: date | None = None


class AdminResetPasswordRequest(BaseModel):
    """Input shape for admin-forced password reset."""
    new_password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    """Input shape for public reader signup — role is always READER."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: str | None = None  # required to use forgot-password later
    date_of_birth: date | None = None


class ForgotPasswordRequest(BaseModel):
    """Input shape for requesting a password reset."""
    email: str


class LoginRequest(BaseModel):
    """Input shape for the login endpoint."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Output shape after successful login — contains the JWT."""
    access_token: str
    token_type: str = "bearer"