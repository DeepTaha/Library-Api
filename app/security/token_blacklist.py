"""In-memory token blacklist. Stores JTIs of logged-out tokens."""

_blacklisted_jtis: set[str] = set()


def add(jti: str) -> None:
    _blacklisted_jtis.add(jti)


def contains(jti: str) -> bool:
    return jti in _blacklisted_jtis


def clear() -> None:
    _blacklisted_jtis.clear()
