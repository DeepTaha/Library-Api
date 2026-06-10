"""Authentication endpoints — login and registration."""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import AuthService
from app import schemas


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Log in with username + password.
    Returns a JWT access token on success.
    """
    service = AuthService(db)
    token = await service.authenticate(form_data.username, form_data.password)
    return schemas.TokenResponse(access_token=token)