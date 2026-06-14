"""FastAPI dependencies for authentication and authorization."""
from datetime import datetime, timezone

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserRole
from app.repositories.user_repository import UserRepository
from app.security.jwt import decode_access_token
from app.security import token_blacklist
from app.exceptions import InvalidToken, InsufficientPermissions, UserNotFound, AccountSuspended


# This tells FastAPI: "Tokens come in the Authorization header as 'Bearer <token>'."
# The tokenUrl="auth/login" is what powers Swagger's "Authorize" button —
# clicking it sends you to that endpoint to get a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Read the JWT from the request, verify it, load the user from the DB.
    This is the foundation of all authentication.
    """
    payload = decode_access_token(token)

    # Reject tokens that have been explicitly invalidated via logout.
    jti = payload.get("jti")
    if jti and await token_blacklist.contains(db, jti):
        raise InvalidToken()

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise InvalidToken()

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise InvalidToken()

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise InvalidToken()

    # Reject tokens issued before the last credential/privilege change.
    # JWT iat is seconds-precision; strip sub-second part of tokens_valid_from
    # so tokens issued in the same second as a reset are not incorrectly rejected.
    iat = payload.get("iat")
    if iat is not None:
        issued_at = datetime.fromtimestamp(iat, tz=timezone.utc)
        if issued_at < user.tokens_valid_from.replace(microsecond=0):
            raise InvalidToken()

    if user.is_suspended:
        raise AccountSuspended()

    return user


def require_role(*allowed_roles: UserRole):
    """
    Factory function that builds a dependency requiring specific roles.
    
    Usage:
        require_admin = require_role(UserRole.ADMIN)
        require_librarian_or_admin = require_role(UserRole.ADMIN, UserRole.LIBRARIAN)
    """
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise InsufficientPermissions()
        return current_user
    
    return dependency


# Pre-built role dependencies for common cases.
# These are reusable — declare once, use everywhere.
require_admin = require_role(UserRole.ADMIN)
require_librarian = require_role(UserRole.ADMIN, UserRole.LIBRARIAN)
require_any_role = require_role(UserRole.ADMIN, UserRole.LIBRARIAN, UserRole.READER)