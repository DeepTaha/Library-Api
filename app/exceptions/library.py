class BookNotFound(Exception):
    pass


class BookNotAvailable(Exception):
    pass


class BorrowingNotFound(Exception):
    pass


class BorrowLimitExceeded(Exception):
    pass


class DuplicateActiveBorrowing(Exception):
    pass


class BookAlreadyReturned(Exception):
    pass


class AgeRestricted(Exception):
    pass


class AgeVerificationRequired(Exception):
    """Raised when a user has no date_of_birth on file and tries to access age-restricted content."""
    pass


class AccountSuspended(Exception):
    pass


class ExtensionLimitReached(Exception):
    """Raised when a borrowing has already been extended the maximum number of times."""
    pass


class CannotExtendOverdue(Exception):
    """Raised when trying to extend a borrowing that is already overdue."""
    pass
