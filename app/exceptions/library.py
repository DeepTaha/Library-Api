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


class AccountSuspended(Exception):
    pass
