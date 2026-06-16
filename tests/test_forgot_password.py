"""E2E tests for POST /auth/forgot-password."""
import pytest


@pytest.mark.asyncio
async def test_registered_email_returns_200_with_message(client, seeded_reader):
    response = await client.post("/auth/forgot-password", json={"email": "testreader@test.com"})

    assert response.status_code == 200
    assert "reset link" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_unknown_email_returns_200_same_message(client):
    response = await client.post("/auth/forgot-password", json={"email": "nobody@test.com"})

    assert response.status_code == 200
    assert "reset link" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_missing_email_field_returns_422(client):
    response = await client.post("/auth/forgot-password", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reset_token_is_stored_and_linked_to_user(client, seeded_reader, db_session):
    from app.security import reset_tokens
    from app.models.password_reset_token import PasswordResetToken
    from sqlalchemy import select

    await client.post("/auth/forgot-password", json={"email": "testreader@test.com"})

    result = await db_session.execute(select(PasswordResetToken))
    entry = result.scalar_one_or_none()

    assert entry is not None
    assert isinstance(entry.user_id, int)
    user_id = await reset_tokens.get_user_id(db_session, entry.token)
    assert user_id == entry.user_id
