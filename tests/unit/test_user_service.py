"""Unit tests for AuthService.update_user() and admin_reset_password()."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.auth_services import AuthService
from app.exceptions import UserNotFound, UsernameAlreadyExists
from app.models.user import UserRole
from app import schemas


def _make_service():
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    service = AuthService(db)
    service.user_repo = MagicMock()
    return service


def _fake_user(user_id=1, username="alice", role=UserRole.READER):
    user = MagicMock()
    user.id = user_id
    user.username = username
    user.role = role
    user.email = None
    return user


# ---------------------------------------------------------------------------
# update_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_user_changes_role():
    service = _make_service()
    user = _fake_user()
    service.user_repo.get_by_id = AsyncMock(return_value=user)
    service.user_repo.get_by_username = AsyncMock(return_value=None)

    result = await service.update_user(1, schemas.UserUpdate(role=UserRole.LIBRARIAN), acting_admin_id=99)

    assert user.role == UserRole.LIBRARIAN
    service.db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_raises_when_not_found():
    service = _make_service()
    service.user_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(UserNotFound):
        await service.update_user(99, schemas.UserUpdate(role=UserRole.ADMIN), acting_admin_id=99)


@pytest.mark.asyncio
async def test_update_user_raises_on_duplicate_username():
    service = _make_service()
    user = _fake_user(user_id=1)
    other_user = _fake_user(user_id=2, username="bob")

    service.user_repo.get_by_id = AsyncMock(return_value=user)
    service.user_repo.get_by_username = AsyncMock(return_value=other_user)

    with pytest.raises(UsernameAlreadyExists):
        await service.update_user(1, schemas.UserUpdate(username="bob"), acting_admin_id=99)


# ---------------------------------------------------------------------------
# admin_reset_password
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_reset_password_hashes_new_password():
    service = _make_service()
    user = _fake_user()
    service.user_repo.get_by_id = AsyncMock(return_value=user)

    await service.admin_reset_password(1, "newsecurepass")

    assert user.hashed_password != "newsecurepass"
    assert user.hashed_password.startswith("$2b$")
    service.db.commit.assert_called_once()
