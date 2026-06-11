"""Unit tests for AuthService.register() — repo and DB are mocked."""
import pytest
from unittest.mock import AsyncMock, MagicMock, ANY

from app.services.auth_services import AuthService
from app.exceptions import UsernameAlreadyExists
from app.models.user import UserRole


def _make_service():
    """Build an AuthService with a fully mocked db and user_repo."""
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    service = AuthService(db)
    service.user_repo = MagicMock()
    return service


@pytest.mark.asyncio
async def test_register_creates_user_with_reader_role():
    service = _make_service()
    service.user_repo.get_by_username = AsyncMock(return_value=None)

    fake_user = MagicMock()
    fake_user.role = UserRole.READER
    service.user_repo.create = AsyncMock(return_value=fake_user)

    result = await service.register("alice", "password123")

    service.user_repo.create.assert_called_once_with(
        username="alice",
        hashed_password=ANY,   # bcrypt hash — we don't know the exact value
        role=UserRole.READER,
        email=None,
    )
    assert result.role == UserRole.READER


@pytest.mark.asyncio
async def test_register_raises_on_duplicate_username():
    service = _make_service()
    service.user_repo.get_by_username = AsyncMock(return_value=MagicMock())

    with pytest.raises(UsernameAlreadyExists):
        await service.register("alice", "password123")


@pytest.mark.asyncio
async def test_register_hashes_password_before_storing():
    service = _make_service()
    service.user_repo.get_by_username = AsyncMock(return_value=None)

    fake_user = MagicMock()
    service.user_repo.create = AsyncMock(return_value=fake_user)

    await service.register("bob", "plaintext")

    _, kwargs = service.user_repo.create.call_args
    assert kwargs["hashed_password"] != "plaintext"
    assert kwargs["hashed_password"].startswith("$2b$")  # bcrypt prefix


@pytest.mark.asyncio
async def test_register_commits_and_refreshes():
    service = _make_service()
    service.user_repo.get_by_username = AsyncMock(return_value=None)
    service.user_repo.create = AsyncMock(return_value=MagicMock())

    await service.register("charlie", "password123")

    service.db.commit.assert_called_once()
    service.db.refresh.assert_called_once()
