class BookNotFound(Exception):
    """Raised when a book lookup by id returns nothing."""
    pass

class BookNotAvailable(Exception):
    """Raised when someone tries to borrow a book with zero copies left."""
    pass

class BorrowingNotFound(Exception):
    """Raised when a borrowing lookup by id returns nothing."""

    pass

class BorrowLimitExceeded(Exception):
    """Raised when user tries to have more than three active borrowings."""
    pass 

class DuplicateActiveBorrowing(Exception):
    """Raised when user haven't returned the book and tries to borrow the same book."""
    pass