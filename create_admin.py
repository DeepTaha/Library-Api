"""Create the initial admin user. Run this once."""
import asyncio
import getpass
import os
import sys
from app.database import SessionLocal
from app.services import AuthService
from app.schemas import UserCreate
from app.models import UserRole


async def main():
    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Enter admin password: ")
        confirm = getpass.getpass("Confirm admin password: ")
        if password != confirm:
            print("Passwords do not match.", file=sys.stderr)
            sys.exit(1)
    if len(password) < 12:
        print("Password must be at least 12 characters.", file=sys.stderr)
        sys.exit(1)

    async with SessionLocal() as db:
        service = AuthService(db)
        try:
            user = await service.create_user(UserCreate(
                username="admin",
                password=password,
                role=UserRole.ADMIN,
            ))
            print(f"Admin user created: id={user.id}, username={user.username}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())