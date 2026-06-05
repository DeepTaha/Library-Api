class BookNotFound(Exception):
    """Raised when a book lookup by id returns nothing."""
    pass

class BookNotAvailable(Exception):
    """Raised when someone tries to borrow a book with zero copies left."""
    pass

class BorrowingNotFound(Exception):
    """Raised when a borrowing lookup by id returns nothing."""

    pass
