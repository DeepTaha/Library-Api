"""Unit tests for JWT creation and verification."""
import pytest
from datetime import datetime, timezone, timedelta
from jose import jwt as jose_jwt

from app.security.jwt import create_access_token, decode_access_token
from app.config import SECRET_KEY, ALGORITHM
from app.exceptions import InvalidToken


def test_create_token_returns_string():
    """Token creation should return a non-empty string."""
    token = create_access_token(user_id=1, role="admin")
    assert isinstance(token, str)
    assert len(token) > 0


def test_token_has_three_parts():
    """JWTs have three dot-separated parts: header.payload.signature."""
    token = create_access_token(user_id=1, role="admin")
    parts = token.split(".")
    assert len(parts) == 3


def test_decode_invalid_token_raises_error():
    """A garbage token should raise InvalidToken."""
    with pytest.raises(InvalidToken):
        decode_access_token("this-is-not-a-valid-token")



def test_decode_expired_token_raises_error():
    """An expired token should fail verification."""
    # Build a token that already expired in the past
    expired_payload = {
        "sub": "1",
        "role": "admin",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_token = jose_jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    with pytest.raises(InvalidToken):
        decode_access_token(expired_token)


def test_different_users_get_different_tokens():
    """Two users should never receive identical tokens."""
    token1 = create_access_token(user_id=1, role="admin")
    token2 = create_access_token(user_id=2, role="reader")
    assert token1 != token2