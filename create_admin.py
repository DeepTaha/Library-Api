"""Create the initial admin user. Run this once."""
import asyncio
from app.database import SessionLocal
from app.services import AuthService
from app.schemas import UserCreate
from app.models import UserRole


async def main():
    async with SessionLocal() as db:
        service = AuthService(db)
        try:
            user = await service.create_user(UserCreate(
                username="admin",
                password="admin12345",
                role=UserRole.ADMIN,
            ))
            print(f"Admin user created: id={user.id}, username={user.username}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())