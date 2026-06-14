"""DB-backed store for password-reset tokens. Survives restarts and works across all workers."""
"""just like repository"""
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.password_reset_token import PasswordResetToken

RESET_TOKEN_EXPIRE = timedelta(hours=1)


async def create(db: AsyncSession, user_id: int) -> str:
    token = str(uuid.uuid4())
    db.add(PasswordResetToken(
        token=token,
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + RESET_TOKEN_EXPIRE,
    ))
    await db.commit()
    return token


async def get_user_id(db: AsyncSession, token: str) -> int | None:
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == token)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        return None
    if datetime.now(timezone.utc) > entry.expires_at:
        await db.delete(entry)
        await db.commit()
        return None
    return entry.user_id


async def consume(db: AsyncSession, token: str) -> None:
    """Remove the token after it has been used (one-time use)."""
    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.token == token))
    await db.commit()


async def purge_expired(db: AsyncSession) -> int:
    result = await db.execute(
        delete(PasswordResetToken).where(PasswordResetToken.expires_at <= datetime.now(timezone.utc))
    )
    await db.commit()
    return result.rowcount
