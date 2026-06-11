"""Authentication endpoints — login and logout."""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import AuthService
from app.security.dependencies import oauth2_scheme, get_current_user
from app.security.jwt import decode_access_token
from app.security import token_blacklist
from app.models import User
from app import schemas


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
async def register(
    user_data: schemas.RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.register(user_data.username, user_data.password, user_data.email, user_data.date_of_birth)


@router.post("/forgot-password", status_code=200)
async def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    token = await service.forgot_password(request.email)
    # Always the same message — never reveal whether the email is registered.
    # reset_token is returned here for development/testing only.
    # In production: email the token as a link and remove it from this response.
    return {
        "message": "If that email is registered, a reset link has been sent.",
        "reset_token": token,
    }


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    token = await service.authenticate(form_data.username, form_data.password)
    return schemas.TokenResponse(access_token=token)


@router.post("/logout", status_code=200)
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
):
    payload = decode_access_token(token)
    jti = payload.get("jti")
    if jti:
        token_blacklist.add(jti)
    return {"message": "Logged out successfully"}