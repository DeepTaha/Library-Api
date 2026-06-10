"""Authentication and authorization exceptions."""


class InvalidCredentials(Exception):
    """Raised when login fails."""
    pass


class InvalidToken(Exception):
    """Raised when a JWT is missing, expired, or malformed."""
    pass


class InsufficientPermissions(Exception):
    """Raised when a user doesn't have the required role for an action."""
    pass


class UserNotFound(Exception):
    """Raised when a user lookup returns nothing."""
    pass


class UsernameAlreadyExists(Exception):
    """Raised when trying to create a user with a taken username."""
    pass