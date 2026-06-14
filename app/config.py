"""Application configuration — secrets, settings, constants."""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

# The algorithm used to sign JWTs.
# HS256 = HMAC with SHA-256. Fast, secure, uses a shared secret.
ALGORITHM = "HS256"

# How long a token is valid before the user has to log in again.
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ACCESS_TOKEN_EXPIRE = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)