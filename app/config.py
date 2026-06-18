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

# Safepay Payment Gateway
SAFEPAY_API_KEY        = os.getenv("SAFEPAY_API_KEY")
SAFEPAY_SECRET_KEY     = os.getenv("SAFEPAY_SECRET_KEY")
SAFEPAY_WEBHOOK_SECRET = os.getenv("SAFEPAY_WEBHOOK_SECRET")
SAFEPAY_SANDBOX        = os.getenv("SAFEPAY_SANDBOX", "true") == "true"
SAFEPAY_SUCCESS_URL    = os.getenv("SAFEPAY_SUCCESS_URL", "http://localhost:8000/payments/success")
SAFEPAY_CANCEL_URL     = os.getenv("SAFEPAY_CANCEL_URL", "http://localhost:8000/payments/cancel")

# These URLs are derived from the sandbox flag — no need to set them manually in .env
SAFEPAY_BASE_URL     = "https://sandbox.api.getsafepay.com" if SAFEPAY_SANDBOX else "https://api.getsafepay.com"
SAFEPAY_CHECKOUT_URL = "https://sandbox.api.getsafepay.com/embedded/" if SAFEPAY_SANDBOX else "https://getsafepay.com/embedded/"

# Fine rate in PKR per day overdue
FINE_RATE_PER_DAY = int(os.getenv("FINE_RATE_PER_DAY", "10"))