"""Application configuration — secrets, settings, constants."""
import os
from datetime import timedelta

# JWT settings
# In production, NEVER hardcode this. Use an environment variable.
# For now, we keep a default so the app can start without setup.
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "your-secret-key-change-this-in-production-please-make-it-long-and-random"
)

# The algorithm used to sign JWTs.
# HS256 = HMAC with SHA-256. Fast, secure, uses a shared secret.
ALGORITHM = "HS256"

# How long a token is valid before the user has to log in again.
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ACCESS_TOKEN_EXPIRE = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)