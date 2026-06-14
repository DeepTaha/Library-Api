"""DB-backed token blacklist. Survives restarts and works across all workers."""
"""just like repository"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.blacklisted_token import BlacklistedToken


async def add(db: AsyncSession, jti: str, expires_at: datetime) -> None:
    db.add(BlacklistedToken(jti=jti, expires_at=expires_at))
    await db.commit()


async def contains(db: AsyncSession, jti: str) -> bool:
    result = await db.execute(select(BlacklistedToken.jti).where(BlacklistedToken.jti == jti))
    return result.scalar() is not None


async def purge_expired(db: AsyncSession) -> int:
    result = await db.execute(
        delete(BlacklistedToken).where(BlacklistedToken.expires_at <= datetime.now(timezone.utc))
    )
    await db.commit()
    return result.rowcount
