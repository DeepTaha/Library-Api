# tests/conftest.py
import os

# CRITICAL: set this BEFORE importing anything from your app
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:lmessi10@localhost:5432/library_test"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from main import app
from database import get_db
import models  # noqa


# Create a separate engine for the test DB
test_engine = create_async_engine(os.environ["DATABASE_URL"])
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


# Override get_db to use the test session
async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Tell the app to use the test DB instead of the real one
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    """Provides an HTTP client that hits our app in-process."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """Wipes the test DB before each test. Runs automatically (autouse=True)."""
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE borrowings, books RESTART IDENTITY CASCADE"))
    yield


@pytest_asyncio.fixture
async def add_book(client):
    """Helper that adds a book and returns its id."""
    async def _add_book(title="Test Book", author="Test Author", total=3, available=3):
        response = await client.post("/books/", json={
            "title": title,
            "author": author,
            "total_copies": total,
            "available_copies": available,
        })
        assert response.status_code == 200
        return response.json()
    return _add_book