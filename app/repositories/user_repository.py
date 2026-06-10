"""Database queries for users."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, username: str, hashed_password: str, role: str) -> User:
        user = User(
            username=username,
            hashed_password=hashed_password,
            role=role,
        )
        self.db.add(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def list_all(self, offset: int, limit: int):
        result = await self.db.execute(
            select(User).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def delete(self, user: User) -> None:
        await self.db.delete(user)