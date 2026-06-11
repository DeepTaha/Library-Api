"""In-memory store for password-reset tokens."""
import uuid
from datetime import datetime, timezone, timedelta

RESET_TOKEN_EXPIRE = timedelta(hours=1)

# token string → {user_id, expires_at}
_store: dict[str, dict] = {}


def create(user_id: int) -> str:
    token = str(uuid.uuid4())
    _store[token] = {
        "user_id": user_id,
        "expires_at": datetime.now(timezone.utc) + RESET_TOKEN_EXPIRE,
    }
    return token


def get_user_id(token: str) -> int | None:
    entry = _store.get(token)
    if entry is None:
        return None
    if datetime.now(timezone.utc) > entry["expires_at"]:
        del _store[token]
        return None
    return entry["user_id"]


def consume(token: str) -> None:
    """Remove the token after it has been used (one-time use)."""
    _store.pop(token, None)


def clear() -> None:
    _store.clear()
