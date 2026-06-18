class FineNotFound(Exception):
    pass


class FineAlreadyPaid(Exception):
    pass


class FineNotBelongToUser(Exception):
    pass


class PaymentNotFound(Exception):
    pass


class InvalidPaymentCallback(Exception):
    """Raised when a Safepay webhook arrives with a signature that does not match."""
    pass


class OutstandingFineExists(Exception):
    """Raised when a user tries to borrow while they have an unpaid fine."""
    pass


class SafepayAPIError(Exception):
    """Raised when Safepay's API returns a non-ok response during tracker creation."""
    pass
