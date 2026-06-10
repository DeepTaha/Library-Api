"""JWT creation and verification."""
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE
from app.exceptions import InvalidToken


def create_access_token(user_id: int, role: str) -> str:
    """
    Create a signed JWT containing the user's id and role.
    The token expires after ACCESS_TOKEN_EXPIRE (set in config).
    """
    expire = datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE
    
    payload = {
        "sub": str(user_id),   # "sub" = subject — the standard JWT field for "who this token is about"
        "role": role,
        "exp": expire,         # "exp" = expiration time — the standard JWT field for when it expires
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> dict:
    """
    Verify and decode a JWT.
    Returns the payload dict.
    Raises InvalidToken if the token is invalid, expired, or tampered with.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Catches all JWT problems: bad signature, expired, malformed, etc.
        raise InvalidToken()