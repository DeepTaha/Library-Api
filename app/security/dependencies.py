"""FastAPI dependencies for authentication and authorization."""
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserRole
from app.repositories.user_repository import UserRepository
from app.security.jwt import decode_access_token
from app.exceptions import InvalidToken, InsufficientPermissions, UserNotFound


# This tells FastAPI: "Tokens come in the Authorization header as 'Bearer <token>'."
# The tokenUrl="auth/login" is what powers Swagger's "Authorize" button — 
# clicking it sends you to that endpoint to get a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# extracts and verify the token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Read the JWT from the request, verify it, load the user from the DB.
    This is the foundation of all authentication.
    """
    # Decode and verify the JWT (raises InvalidToken if bad)
    payload = decode_access_token(token)
    
    # Extract the user id from the payload
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise InvalidToken()
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise InvalidToken()
    
    # Look up the user in the database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        # Token is valid but the user was deleted — treat as invalid.
        raise InvalidToken()
    
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