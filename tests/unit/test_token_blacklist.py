"""Unit tests for the DB-backed token blacklist module."""
from datetime import datetime, timezone, timedelta

import pytest

from app.models.blacklisted_token import BlacklistedToken
from app.security import token_blacklist
from app.security.jwt import create_access_token, decode_access_token


@pytest.mark.asyncio
async def test_contains_returns_false_for_unknown_jti(db_session):
    assert await token_blacklist.contains(db_session, "nonexistent-jti") is False


@pytest.mark.asyncio
async def test_add_then_contains_returns_true(db_session):
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await token_blacklist.add(db_session, "abc-123", expires_at)
    assert await token_blacklist.contains(db_session, "abc-123") is True


@pytest.mark.asyncio
async def test_contains_returns_false_for_different_jti(db_session):
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await token_blacklist.add(db_session, "jti-A", expires_at)
    assert await token_blacklist.contains(db_session, "jti-B") is False


@pytest.mark.asyncio
async def test_purge_removes_expired_rows(db_session):
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    future = datetime.now(timezone.utc) + timedelta(hours=1)

    db_session.add(BlacklistedToken(jti="expired-jti", expires_at=past))
    db_session.add(BlacklistedToken(jti="live-jti", expires_at=future))
    await db_session.commit()

    count = await token_blacklist.purge_expired(db_session)

    assert count == 1
    assert not await token_blacklist.contains(db_session, "expired-jti")
    assert await token_blacklist.contains(db_session, "live-jti")


@pytest.mark.asyncio
async def test_purge_returns_zero_when_nothing_expired(db_session):
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    db_session.add(BlacklistedToken(jti="live-jti", expires_at=future))
    await db_session.commit()

    count = await token_blacklist.purge_expired(db_session)
    assert count == 0


@pytest.mark.asyncio
async def test_purge_empty_table_returns_zero(db_session):
    count = await token_blacklist.purge_expired(db_session)
    assert count == 0


def test_create_access_token_includes_unique_jti():
    token_a = create_access_token(user_id=1, role="ADMIN")
    token_b = create_access_token(user_id=1, role="ADMIN")
    jti_a = decode_access_token(token_a)["jti"]
    jti_b = decode_access_token(token_b)["jti"]
    assert jti_a != jti_b
