"""Authentication endpoints — login and logout."""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import AuthService
from app.security.dependencies import oauth2_scheme, get_current_user
from app.security.jwt import decode_access_token
from app.security import token_blacklist
from app.security.rate_limit import limiter
from app.models import User
from app import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: schemas.RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.register(user_data.username, user_data.password, user_data.email, user_data.date_of_birth)


@router.post("/forgot-password", status_code=200)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    body: schemas.ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    token = await service.forgot_password(body.email)
    if token is not None:
        # In production: send token as a link in an email instead of logging it.
        logger.info("Password reset token for %s: %s", body.email, token)
    # Always return the same response — never reveal whether the email is registered.
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=200)
async def reset_password(
    request: schemas.ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.reset_password(request.token, request.new_password)
    return {"message": "Password has been reset successfully."}


@router.post("/login", response_model=schemas.TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
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
    db: AsyncSession = Depends(get_db),
):
    payload = decode_access_token(token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        await token_blacklist.add(db, jti, expires_at)
    return {"message": "Logged out successfully"}