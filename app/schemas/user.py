"""Pydantic schemas for user input and output."""
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.user import UserRole

_MAX_HUMAN_AGE_YEARS = 130


def _validate_dob(v: date | None) -> date | None:
    if v is None:
        return v
    today = date.today()
    if v >= today:
        raise ValueError("Date of birth must be in the past")
    earliest = today.replace(year=today.year - _MAX_HUMAN_AGE_YEARS)
    if v < earliest:
        raise ValueError("Date of birth is not within a valid range")
    return v


class UserCreate(BaseModel):
    """Input shape when an admin creates a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=1024)
    role: UserRole = UserRole.READER
    email: EmailStr | None = None
    date_of_birth: date | None = None

    @field_validator("date_of_birth")
    @classmethod
    def dob_must_be_valid(cls, v):
        return _validate_dob(v)


class UserResponse(BaseModel):
    """Output shape when returning user info — NEVER includes the password."""
    id: int
    username: str
    role: UserRole
    email: EmailStr | None
    date_of_birth: date | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Input shape for PATCH /users/{id} — all fields optional."""
    username: str | None = Field(None, min_length=3, max_length=50)
    role: UserRole | None = None
    email: EmailStr | None = None
    date_of_birth: date | None = None

    @field_validator("date_of_birth")
    @classmethod
    def dob_must_be_valid(cls, v):
        return _validate_dob(v)


class AdminResetPasswordRequest(BaseModel):
    """Input shape for admin-forced password reset."""
    new_password: str = Field(..., min_length=8, max_length=1024)


class RegisterRequest(BaseModel):
    """Input shape for public reader signup — role is always READER."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=1024)
    email: EmailStr | None = None  # required to use forgot-password later
    date_of_birth: date | None = None

    @field_validator("date_of_birth")
    @classmethod
    def dob_must_be_valid(cls, v):
        return _validate_dob(v)


class ForgotPasswordRequest(BaseModel):
    """Input shape for requesting a password reset."""
    email: EmailStr


class LoginRequest(BaseModel):
    """Input shape for the login endpoint."""
    username: str
    password: str = Field(..., max_length=1024)


class TokenResponse(BaseModel):
    """Output shape after successful login — contains the JWT."""
    access_token: str
    token_type: str = "bearer"


class ResetPasswordRequest(BaseModel):
    """Input shape for completing a password reset."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=1024)