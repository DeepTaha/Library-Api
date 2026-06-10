"""Unit tests for password hashing and verification."""
from app.security.password import hash_password, verify_password


def test_hash_password_returns_string():
    """The hash function should return a non-empty string."""
    result = hash_password("mypassword123")
    assert isinstance(result, str)
    assert len(result) > 0


def test_hash_is_not_the_plain_password():
    """Critical security check — the hash must not equal the plain password."""
    plain = "mypassword123"
    hashed = hash_password(plain)
    assert hashed != plain


def test_same_password_produces_different_hashes():
    """
    Bcrypt uses a random salt, so the same password
    hashed twice should produce two different hashes.
    """
    hash1 = hash_password("samepassword")
    hash2 = hash_password("samepassword")
    assert hash1 != hash2


def test_verify_correct_password_returns_true():
    """A correct password should verify successfully."""
    hashed = hash_password("mypassword123")
    assert verify_password("mypassword123", hashed) is True


def test_verify_wrong_password_returns_false():
    """A wrong password should fail verification."""
    hashed = hash_password("mypassword123")
    assert verify_password("wrongpassword", hashed) is False


def test_verify_is_case_sensitive():
    """Passwords are case-sensitive."""
    hashed = hash_password("MyPassword")
    assert verify_password("mypassword", hashed) is False
    assert verify_password("MyPassword", hashed) is True