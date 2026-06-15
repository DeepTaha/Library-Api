"""User management endpoints — admin only."""
from fastapi import APIRouter, Depends, Query
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
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
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


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get a single user by id. Admin only."""
    service = AuthService(db)
    return await service.get_user_by_id(user_id)


@router.patch("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    update_data: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a user's username, role, or email. Admin only."""
    service = AuthService(db)
    return await service.update_user(user_id, update_data, acting_admin_id=current_user.id)


@router.post("/{user_id}/reset-password", status_code=200)
async def admin_reset_password(
    user_id: int,
    body: schemas.AdminResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Force a password reset for any user. Admin only."""
    service = AuthService(db)
    await service.admin_reset_password(user_id, body.new_password)
    return {"message": "Password reset successfully"}


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a user. Admin only."""
    service = AuthService(db)
    await service.delete_user(user_id, acting_admin_id=current_user.id)