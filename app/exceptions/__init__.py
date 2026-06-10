from app.exceptions.library import (
    BookNotFound,
    BookNotAvailable,
    BorrowingNotFound,
    BorrowLimitExceeded,
    DuplicateActiveBorrowing,
    BookAlreadyReturned,
)
from app.exceptions.auth import (
    InvalidCredentials,
    InvalidToken,
    InsufficientPermissions,
    UserNotFound,
    UsernameAlreadyExists,
)

__all__ = [
    "BookNotFound",
    "BookNotAvailable",
    "BorrowingNotFound",
    "BorrowLimitExceeded",
    "DuplicateActiveBorrowing",
]
