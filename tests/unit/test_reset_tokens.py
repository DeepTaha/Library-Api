"""Unit tests for the DB-backed reset_tokens module."""
from datetime import datetime, timezone, timedelta

import pytest

from app.models.password_reset_token import PasswordResetToken
from app.security import reset_tokens


@pytest.mark.asyncio
async def test_create_returns_token_string(db_session, seeded_user_id):
    token = await reset_tokens.create(db_session, user_id=seeded_user_id)
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_get_user_id_returns_correct_user(db_session, seeded_user_id):
    token = await reset_tokens.create(db_session, user_id=seeded_user_id)
    assert await reset_tokens.get_user_id(db_session, token) == seeded_user_id


@pytest.mark.asyncio
async def test_unknown_token_returns_none(db_session):
    assert await reset_tokens.get_user_id(db_session, "does-not-exist") is None


@pytest.mark.asyncio
async def test_consume_invalidates_token(db_session, seeded_user_id):
    token = await reset_tokens.create(db_session, user_id=seeded_user_id)
    await reset_tokens.consume(db_session, token)
    assert await reset_tokens.get_user_id(db_session, token) is None


@pytest.mark.asyncio
async def test_expired_token_returns_none(db_session, seeded_user_id):
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.add(PasswordResetToken(token="expired-tok", user_id=seeded_user_id, expires_at=past))
    await db_session.commit()

    assert await reset_tokens.get_user_id(db_session, "expired-tok") is None


@pytest.mark.asyncio
async def test_purge_removes_expired_tokens(db_session, seeded_user_id):
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    future = datetime.now(timezone.utc) + timedelta(hours=1)

    db_session.add(PasswordResetToken(token="expired-tok", user_id=seeded_user_id, expires_at=past))
    db_session.add(PasswordResetToken(token="live-tok", user_id=seeded_user_id, expires_at=future))
    await db_session.commit()

    count = await reset_tokens.purge_expired(db_session)

    assert count == 1
    assert await reset_tokens.get_user_id(db_session, "expired-tok") is None
    assert await reset_tokens.get_user_id(db_session, "live-tok") == seeded_user_id
