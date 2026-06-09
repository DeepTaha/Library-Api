import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:lmessi10@localhost:5432/library_test")

engine = create_async_engine(DATABASE_URL, echo=False)

SessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
)

class Base(DeclarativeBase):
    pass

# Called per request. Closes automatically after response (Step 8)
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
