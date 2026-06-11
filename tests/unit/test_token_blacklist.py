"""Unit tests for the token blacklist module and logout-related JWT behaviour."""
import pytest
from app.security import token_blacklist
from app.security.jwt import create_access_token, decode_access_token


@pytest.fixture(autouse=True)
def clean_blacklist():
    token_blacklist.clear()
    yield
    token_blacklist.clear()


def test_contains_returns_false_for_unknown_jti():
    assert token_blacklist.contains("nonexistent-jti") is False


def test_add_then_contains_returns_true():
    token_blacklist.add("abc-123")
    assert token_blacklist.contains("abc-123") is True


def test_clear_empties_the_blacklist():
    token_blacklist.add("jti-1")
    token_blacklist.add("jti-2")
    token_blacklist.clear()
    assert token_blacklist.contains("jti-1") is False
    assert token_blacklist.contains("jti-2") is False


def test_create_access_token_includes_jti():
    token = create_access_token(user_id=1, role="ADMIN")
    payload = decode_access_token(token)
    assert "jti" in payload
    assert payload["jti"]
