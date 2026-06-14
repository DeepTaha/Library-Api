import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_async_engine(DATABASE_URL, echo=False)

SessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
)

class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
