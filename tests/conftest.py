# tests/conftest.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: set these BEFORE importing anything from your app
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:lmessi10@localhost:5432/library_test"
os.environ["RATELIMIT_ENABLED"] = "0"  # disable rate limiting in the test suite

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from app.main import app
from app.database import get_db, Base
from app import models  # noqa: F401

# Module-level reference so fixtures like `seeded_admin` and `db_session` can create sessions.
_test_session_factory = None


@pytest_asyncio.fixture(loop_scope="function", autouse=True)
async def setup_test_db():
    global _test_session_factory

    engine = create_async_engine(os.environ["DATABASE_URL"])
    _test_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with _test_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    await engine.dispose()
    app.dependency_overrides.clear()
    _test_session_factory = None


@pytest_asyncio.fixture(loop_scope="function")
async def client():
    """Provides an HTTP client that hits our app in-process."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(loop_scope="function")
async def add_book(client):
    """Helper that adds a book and returns its data. Pass headers= for auth."""
    async def _add_book(title="Test Book", author="Test Author", total=3, available=3, headers=None):
        response = await client.post("/books/", json={
            "title": title,
            "author": author,
            "total_copies": total,
            "available_copies": available,
        }, headers=headers or {})
        assert response.status_code in (200, 201)
        return response.json()
    return _add_book


@pytest_asyncio.fixture(loop_scope="function")
async def seeded_admin():
    """Creates an ADMIN user directly in the test DB and returns credentials."""
    from app.models.user import User, UserRole
    from app.security.password import hash_password

    async with _test_session_factory() as session:
        user = User(
            username="testadmin",
            hashed_password=hash_password("testpass123"),
            role=UserRole.ADMIN,
            email="testadmin@test.com",
        )
        session.add(user)
        await session.commit()

    return {"username": "testadmin", "password": "testpass123"}


@pytest_asyncio.fixture(loop_scope="function")
async def seeded_reader():
    """Creates a READER user directly in the test DB and returns credentials."""
    from app.models.user import User, UserRole
    from app.security.password import hash_password

    async with _test_session_factory() as session:
        user = User(
            username="testreader",
            hashed_password=hash_password("readerpass123"),
            role=UserRole.READER,
            email="testreader@test.com",
        )
        session.add(user)
        await session.commit()

    return {"username": "testreader", "password": "readerpass123"}


@pytest_asyncio.fixture(loop_scope="function")
async def admin_token(client, seeded_admin):
    """Returns a valid JWT for the seeded admin user."""
    resp = await client.post("/auth/login", data=seeded_admin)
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture(loop_scope="function")
async def admin_headers(admin_token):
    """Returns Authorization headers for the seeded admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture(loop_scope="function")
async def reader_token(client, seeded_reader):
    """Returns a valid JWT for the seeded reader user."""
    resp = await client.post("/auth/login", data=seeded_reader)
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture(loop_scope="function")
async def reader_headers(reader_token):
    """Returns Authorization headers for the seeded reader user."""
    return {"Authorization": f"Bearer {reader_token}"}


@pytest_asyncio.fixture(loop_scope="function")
async def db_session():
    """Provides a direct DB session for async unit-style tests."""
    async with _test_session_factory() as session:
        yield session


@pytest_asyncio.fixture(loop_scope="function")
async def seeded_user_id():
    """Creates a minimal user and returns its DB id, for FK-constrained unit tests."""
    from app.models.user import User, UserRole
    from app.security.password import hash_password

    async with _test_session_factory() as session:
        user = User(
            username="fxtuser",
            hashed_password=hash_password("x"),
            role=UserRole.READER,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user.id
