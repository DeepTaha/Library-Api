"""User management endpoints — admin only."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import AuthService
from app.security import require_admin, require_any_role
from app.models import User
from app import schemas


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=schemas.UserResponse, status_code=201)
async def create_user(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new user. Admin only."""
    service = AuthService(db)
    return await service.create_user(user_data)


@router.get("/", response_model=list[schemas.UserResponse])
async def list_users(
    offset: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all users. Admin only."""
    service = AuthService(db)
    return await service.list_users(offset, limit)


@router.get("/me", response_model=schemas.UserResponse)
async def get_my_profile(
    current_user: User = Depends(require_any_role),
):
    """Get the currently logged-in user's profile."""
    return current_user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a user. Admin only."""
    service = AuthService(db)
    await service.delete_user(user_id)