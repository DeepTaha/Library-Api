"""Password hashing and verification using bcrypt."""
import base64
import hashlib

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _prehash(plain: str) -> str:
    # bcrypt silently truncates at 72 bytes; SHA-256 collapses the input to
    # 32 bytes so every bit of the original password affects the digest.
    digest = hashlib.sha256(plain.encode()).digest()
    return base64.b64encode(digest).decode()


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(_prehash(plain_password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_prehash(plain_password), hashed_password)