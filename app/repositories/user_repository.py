"""Database queries for users."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.models import User, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, username: str, hashed_password: str, role: str, email: str | None = None, date_of_birth=None) -> User:
        user = User(
            username=username,
            hashed_password=hashed_password,
            role=role,
            email=email,
            date_of_birth=date_of_birth,
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

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def list_all(self, offset: int, limit: int):
        result = await self.db.execute(
            select(User).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def count_admins(self) -> int:
        result = await self.db.execute(
            select(func.count()).where(User.role == UserRole.ADMIN)
        )
        return result.scalar_one()

    async def delete(self, user: User) -> None:
        await self.db.delete(user)