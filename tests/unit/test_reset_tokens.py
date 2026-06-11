"""Unit tests for the reset_tokens module."""
import pytest
from app.security import reset_tokens


@pytest.fixture(autouse=True)
def clean_store():
    reset_tokens.clear()
    yield
    reset_tokens.clear()


def test_create_and_get_user_id():
    token = reset_tokens.create(user_id=42)
    assert reset_tokens.get_user_id(token) == 42


def test_unknown_token_returns_none():
    assert reset_tokens.get_user_id("does-not-exist") is None


def test_consume_invalidates_token():
    token = reset_tokens.create(user_id=7)
    reset_tokens.consume(token)
    assert reset_tokens.get_user_id(token) is None


def test_clear_removes_all_tokens():
    token_a = reset_tokens.create(user_id=1)
    token_b = reset_tokens.create(user_id=2)
    reset_tokens.clear()
    assert reset_tokens.get_user_id(token_a) is None
    assert reset_tokens.get_user_id(token_b) is None
