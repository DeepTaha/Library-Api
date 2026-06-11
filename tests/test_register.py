"""E2E tests for POST /auth/register."""
import pytest


@pytest.mark.asyncio
async def test_register_creates_reader_account(client):
    response = await client.post("/auth/register", json={
        "username": "newuser",
        "password": "securepass123",
    })

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "newuser"
    assert body["role"] == "reader"
    assert "id" in body
    assert "password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_username_returns_400(client):
    payload = {"username": "alice", "password": "password123"}
    await client.post("/auth/register", json=payload)

    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert "taken" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_rejects_short_password(client):
    response = await client.post("/auth/register", json={
        "username": "bob",
        "password": "short",
    })

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_registered_user_can_login(client):
    await client.post("/auth/register", json={
        "username": "carol",
        "password": "mypassword123",
    })

    login = await client.post("/auth/login", data={
        "username": "carol",
        "password": "mypassword123",
    })

    assert login.status_code == 200
    assert "access_token" in login.json()
