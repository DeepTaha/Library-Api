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


class EmailAlreadyExists(Exception):
    """Raised when trying to create a user with an already-registered email."""
    pass


class InvalidResetToken(Exception):
    """Raised when a password-reset token is missing, expired, or already used."""
    pass


class CannotSelfModify(Exception):
    """Raised when an admin tries to delete or demote their own account."""
    pass


class LastAdminProtected(Exception):
    """Raised when an action would leave the system with no admins."""
    pass