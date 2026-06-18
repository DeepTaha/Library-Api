from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.security import require_any_role, require_librarian
from app.models import User, UserRole
from app.models.fine import FineStatus
from app.repositories.fine_repository import FineRepository
from app.schemas.fine import FineResponse, FineWaiveRequest
from app.exceptions import (
    FineNotFound,
    FineAlreadyPaid,
    InsufficientPermissions,
)

router = APIRouter(prefix="/fines", tags=["fines"])


@router.get("/me", response_model=list[FineResponse])
async def get_my_fines(
    status: Optional[str] = Query(None, description="Filter by status: pending, paid, waived"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """Get all fines for the logged-in user, optionally filtered by status."""
    fine_repo = FineRepository(db)
    fine_status = FineStatus(status) if status else None
    return await fine_repo.list_by_user(current_user.id, status=fine_status)


@router.get("/", response_model=list[FineResponse])
async def list_all_fines(
    status: Optional[str] = Query(None, description="Filter by status: pending, paid, waived"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """List all fines across all users. Librarian/admin only."""
    fine_repo = FineRepository(db)
    fine_status = FineStatus(status) if status else None
    return await fine_repo.list_all(status=fine_status, offset=offset, limit=limit)


@router.get("/{fine_id}", response_model=FineResponse)
async def get_fine(
    fine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any_role),
):
    """Get a single fine. Readers can only see their own; librarian/admin can see any."""
    fine_repo = FineRepository(db)
    fine = await fine_repo.get_by_id(fine_id)

    if not fine:
        raise FineNotFound()

    if (fine.user_id != current_user.id
            and current_user.role not in (UserRole.ADMIN, UserRole.LIBRARIAN)):
        raise InsufficientPermissions()

    return fine


@router.post("/{fine_id}/waive", response_model=FineResponse)
async def waive_fine(
    fine_id: int,
    body: FineWaiveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_librarian),
):
    """Waive a fine — forgives the amount owed. Librarian/admin only."""
    fine_repo = FineRepository(db)
    fine = await fine_repo.get_by_id(fine_id)

    if not fine:
        raise FineNotFound()

    if fine.status != FineStatus.PENDING:
        raise FineAlreadyPaid()

    fine = await fine_repo.mark_waived(fine_id)
    await db.commit()
    await db.refresh(fine)
    return fine
