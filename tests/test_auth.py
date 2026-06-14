"""E2E tests for POST /auth/logout and the DB-backed token blacklist."""
import pytest
from sqlalchemy import select

from app.models.blacklisted_token import BlacklistedToken
from app.security.jwt import decode_access_token


# ---------------------------------------------------------------------------
# Basic logout behaviour
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_logout_returns_200_with_message(client, reader_headers):
    response = await client.post("/auth/logout", headers=reader_headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}


@pytest.mark.asyncio
async def test_logout_without_token_returns_401(client):
    response = await client.post("/auth/logout")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Token is rejected after logout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_logout_invalidates_token_on_users_me(client, reader_headers):
    await client.post("/auth/logout", headers=reader_headers)
    after = await client.get("/users/me", headers=reader_headers)
    assert after.status_code == 401


@pytest.mark.asyncio
async def test_logout_invalidates_token_on_books_endpoint(client, reader_headers):
    await client.post("/auth/logout", headers=reader_headers)
    after = await client.get("/books/", headers=reader_headers)
    assert after.status_code == 401


@pytest.mark.asyncio
async def test_logout_invalidates_token_on_borrowings_endpoint(client, reader_headers):
    await client.post("/auth/logout", headers=reader_headers)
    after = await client.get("/borrowings/me", headers=reader_headers)
    assert after.status_code == 401


# ---------------------------------------------------------------------------
# Second logout attempt is rejected (token already blacklisted)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_double_logout_second_call_is_401(client, reader_headers):
    first = await client.post("/auth/logout", headers=reader_headers)
    assert first.status_code == 200

    second = await client.post("/auth/logout", headers=reader_headers)
    assert second.status_code == 401


# ---------------------------------------------------------------------------
# New login after logout issues a working fresh token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_new_login_after_logout_issues_fresh_token(client, seeded_reader, reader_headers):
    await client.post("/auth/logout", headers=reader_headers)

    login_resp = await client.post("/auth/login", data=seeded_reader)
    assert login_resp.status_code == 200
    new_token = login_resp.json()["access_token"]

    profile = await client.get("/users/me", headers={"Authorization": f"Bearer {new_token}"})
    assert profile.status_code == 200


# ---------------------------------------------------------------------------
# Concurrent sessions: each token has its own JTI; blacklisting one leaves
# the other untouched.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_logout_one_session_does_not_affect_other(client, seeded_reader):
    resp_a = await client.post("/auth/login", data=seeded_reader)
    resp_b = await client.post("/auth/login", data=seeded_reader)
    token_a = resp_a.json()["access_token"]
    token_b = resp_b.json()["access_token"]

    # Confirm the two tokens carry distinct JTIs
    assert decode_access_token(token_a)["jti"] != decode_access_token(token_b)["jti"]

    # Logout session A
    await client.post("/auth/logout", headers={"Authorization": f"Bearer {token_a}"})

    # Session A is dead
    assert (await client.get("/users/me", headers={"Authorization": f"Bearer {token_a}"})).status_code == 401
    # Session B is still alive
    assert (await client.get("/users/me", headers={"Authorization": f"Bearer {token_b}"})).status_code == 200


# ---------------------------------------------------------------------------
# DB persistence: the JTI row actually lands in blacklisted_tokens
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_jti_persisted_in_db_after_logout(client, reader_token, reader_headers, db_session):
    jti = decode_access_token(reader_token)["jti"]

    await client.post("/auth/logout", headers=reader_headers)

    result = await db_session.execute(
        select(BlacklistedToken).where(BlacklistedToken.jti == jti)
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.jti == jti


@pytest.mark.asyncio
async def test_blacklisted_row_carries_correct_expiry(client, reader_token, reader_headers, db_session):
    payload = decode_access_token(reader_token)
    jti = payload["jti"]
    expected_exp = payload["exp"]  # Unix timestamp

    await client.post("/auth/logout", headers=reader_headers)

    result = await db_session.execute(
        select(BlacklistedToken).where(BlacklistedToken.jti == jti)
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert int(row.expires_at.timestamp()) == expected_exp
