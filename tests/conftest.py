# tests/conftest.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: set this BEFORE importing anything from your app
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:lmessi10@localhost:5432/library_test"

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from app.main import app
from app.database import get_db
from app import models  # noqa: F401


@pytest_asyncio.fixture(loop_scope="function", autouse=True)
async def setup_test_db():
    """Create engine, clean tables, override get_db, all within the test's event loop."""
    # Create a fresh engine for this test's event loop
    engine = create_async_engine(os.environ["DATABASE_URL"])
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    # Clean the tables
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE borrowings, books RESTART IDENTITY CASCADE"))
    
    # Override get_db to use this test's session
    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    # Cleanup: dispose the engine after the test
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(loop_scope="function")
async def client():
    """Provides an HTTP client that hits our app in-process."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(loop_scope="function")
async def add_book(client):
    """Helper that adds a book and returns its id."""
    async def _add_book(title="Test Book", author="Test Author", total=3, available=3):
        response = await client.post("/books/", json={
            "title": title,
            "author": author,
            "total_copies": total,
            "available_copies": available,
        })
        assert response.status_code in (200, 201)
        return response.json()
    return _add_book