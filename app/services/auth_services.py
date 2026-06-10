"""Authentication and user management service."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token
from app.exceptions import (
    InvalidCredentials,
    UserNotFound,
    UsernameAlreadyExists,
)
from app.models import User, UserRole
from app import schemas


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def create_user(self, user_data: schemas.UserCreate) -> User:
        """Create a new user. Used by admins."""
        # Check if username is already taken
        existing = await self.user_repo.get_by_username(user_data.username)
        if existing is not None:
            raise UsernameAlreadyExists()
        
        # Hash the password before storing
        hashed = hash_password(user_data.password)
        
        # Save the user
        user = await self.user_repo.create(
            username=user_data.username,
            hashed_password=hashed,
            role=user_data.role,
        )
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def authenticate(self, username: str, password: str) -> str:
        """
        Verify credentials and return a JWT if valid.
        Raises InvalidCredentials if username or password is wrong.
        """
        user = await self.user_repo.get_by_username(username)
        
        # If username doesn't exist OR password doesn't match → same error.
        # We don't say "username not found" vs "wrong password" — that would
        # leak info about which usernames exist. Always return the same error.
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentials()
        
        # Generate the JWT
        token = create_access_token(user_id=user.id, role=user.role.value)
        return token
    
    async def get_user_by_id(self, user_id: int) -> User:
        """Fetch a user by id. Raises UserNotFound if missing."""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        return user
    
    async def list_users(self, offset: int, limit: int):
        return await self.user_repo.list_all(offset, limit)
    
    async def delete_user(self, user_id: int) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        await self.user_repo.delete(user)
        await self.db.commit()