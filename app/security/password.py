"""Password hashing and verification using bcrypt."""
from passlib.context import CryptContext


# Create a context for password hashing.
# This is the standard way passlib is set up.
# "bcrypt" tells it which algorithm to use.
# "auto" means it'll auto-upgrade old hashes if we ever switch algorithms later.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Turn a plain password into a secure hash.
    Used when creating or updating a user.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches a stored hash.
    Returns True if they match, False otherwise.
    Used during login.
    """
    return pwd_context.verify(plain_password, hashed_password)