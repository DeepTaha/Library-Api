"""Authentication and user management service."""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token
from app.exceptions import (
    InvalidCredentials,
    UserNotFound,
    UsernameAlreadyExists,
    InvalidResetToken,
    AccountSuspended,
)
from app.models import User, UserRole
from app.security import reset_tokens
from app import schemas


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def create_user(self, user_data: schemas.UserCreate) -> User:
        """Create a new user. Used by admins."""
        existing = await self.user_repo.get_by_username(user_data.username)
        if existing is not None:
            raise UsernameAlreadyExists()

        user = await self.user_repo.create(
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
            email=user_data.email,
            date_of_birth=user_data.date_of_birth,
        )
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def register(self, username: str, password: str, email: str | None = None, date_of_birth=None) -> User:
        """Public reader self-signup. Role is always READER."""
        existing = await self.user_repo.get_by_username(username)
        if existing is not None:
            raise UsernameAlreadyExists()

        user = await self.user_repo.create(
            username=username,
            hashed_password=hash_password(password),
            role=UserRole.READER,
            email=email,
            date_of_birth=date_of_birth,
        )
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def forgot_password(self, email: str) -> str | None:
        """
        Create a password-reset token for the user with this email.
        Returns None silently when the email is not registered — callers
        should always respond with the same message to prevent email enumeration.
        The token must never be returned in the HTTP response; callers should
        send it out-of-band (e.g. email) or log it for dev purposes only.
        """
        user = await self.user_repo.get_by_email(email)
        if user is None:
            return None
        return await reset_tokens.create(self.db, user.id)

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Validate the reset token, update the password, and consume the token
        so it cannot be reused.
        Raises InvalidResetToken if the token is missing, expired, or already used.
        """
        user_id = await reset_tokens.get_user_id(self.db, token)
        if user_id is None:
            raise InvalidResetToken()
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            await reset_tokens.consume(self.db, token)
            raise InvalidResetToken()
        user.hashed_password = hash_password(new_password)
        user.tokens_valid_from = datetime.now(timezone.utc)
        await reset_tokens.consume(self.db, token)
        await self.db.commit()

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

        if user.is_suspended:
            raise AccountSuspended()

        # Generate the JWT
        token = create_access_token(user_id=user.id, role=user.role.value)  # builds a JWT payload
        return token
    
    async def get_user_by_id(self, user_id: int) -> User:
        """Fetch a user by id. Raises UserNotFound if missing."""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        return user
    
    async def list_users(self, offset: int, limit: int):
        return await self.user_repo.list_all(offset, limit)
    
    async def update_user(self, user_id: int, update_data: schemas.UserUpdate) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound()

        invalidate_sessions = False

        if update_data.username is not None:
            existing = await self.user_repo.get_by_username(update_data.username)
            if existing is not None and existing.id != user_id:
                raise UsernameAlreadyExists()
            user.username = update_data.username

        if update_data.role is not None and update_data.role != user.role:
            user.role = update_data.role
            invalidate_sessions = True

        if update_data.email is not None:
            user.email = update_data.email

        if update_data.date_of_birth is not None:
            user.date_of_birth = update_data.date_of_birth

        if invalidate_sessions:
            user.tokens_valid_from = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def admin_reset_password(self, user_id: int, new_password: str) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        user.hashed_password = hash_password(new_password)
        user.tokens_valid_from = datetime.now(timezone.utc)
        await self.db.commit()

    async def delete_user(self, user_id: int) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        await self.user_repo.delete(user)
        await self.db.commit()