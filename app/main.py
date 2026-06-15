from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import models  # noqa: F401 — ensures models are registered on Base.metadata
from app.routers import analytics, books, borrowings, admin, auth, users, reports
from app.scheduler import start_scheduler, stop_scheduler
from app.security.rate_limit import limiter
from app.services.library_service import MAX_EXTENSIONS
from app.exceptions import (
    BookNotFound,
    BookNotAvailable,
    BorrowingNotFound,
    BorrowLimitExceeded,
    DuplicateActiveBorrowing,
    AgeRestricted,
    AgeVerificationRequired,
    AccountSuspended,
    ExtensionLimitReached,
    CannotExtendOverdue,
    InvalidCredentials,
    InvalidToken,
    InsufficientPermissions,
    UserNotFound,
    UsernameAlreadyExists,
    EmailAlreadyExists,
    InvalidResetToken,
    CannotSelfModify,
    LastAdminProtected,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Library Book Borrowing System", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# Existing handlers...
@app.exception_handler(AgeRestricted)
async def handle_age_restricted(request: Request, exc: AgeRestricted):
    return JSONResponse(status_code=403, content={"detail": "This book is age-restricted and you do not meet the age requirement"})


@app.exception_handler(AgeVerificationRequired)
async def handle_age_verification_required(request: Request, exc: AgeVerificationRequired):
    return JSONResponse(status_code=403, content={"detail": "This book is age-restricted. Please update your profile with your date of birth to access this content"})


@app.exception_handler(ExtensionLimitReached)
async def handle_extension_limit(request: Request, exc: ExtensionLimitReached):
    return JSONResponse(status_code=400, content={"detail": f"Borrowing cannot be extended more than {MAX_EXTENSIONS} time(s)"})


@app.exception_handler(CannotExtendOverdue)
async def handle_cannot_extend_overdue(request: Request, exc: CannotExtendOverdue):
    return JSONResponse(status_code=400, content={"detail": "Overdue borrowings cannot be extended — please return the book first"})


@app.exception_handler(BookNotFound)
async def handle_book_not_found(request: Request, exc: BookNotFound):
    return JSONResponse(status_code=404, content={"detail": "Book not found"})


@app.exception_handler(BorrowingNotFound)
async def handle_borrowing_not_found(request: Request, exc: BorrowingNotFound):
    return JSONResponse(status_code=404, content={"detail": "Borrowing record not found"})


@app.exception_handler(BookNotAvailable)
async def handle_book_not_available(request: Request, exc: BookNotAvailable):
    return JSONResponse(status_code=400, content={"detail": "No copies available"})


@app.exception_handler(BorrowLimitExceeded)
async def handle_borrow_limit(request: Request, exc: BorrowLimitExceeded):
    return JSONResponse(status_code=400, content={"detail": "User has reached the maximum of 3 active borrowings"})


@app.exception_handler(DuplicateActiveBorrowing)
async def handle_duplicate_borrow(request: Request, exc: DuplicateActiveBorrowing):
    return JSONResponse(status_code=400, content={"detail": "User has already borrowed this book and not returned it"})


@app.exception_handler(AccountSuspended)
async def handle_account_suspended(request: Request, exc: AccountSuspended):
    return JSONResponse(status_code=403, content={"detail": "Your account is on hold due to overdue returns. Return all overdue books to automatically restore borrowing access."})


# New auth handlers
@app.exception_handler(InvalidCredentials)
async def handle_invalid_credentials(request: Request, exc: InvalidCredentials):
    return JSONResponse(status_code=401, content={"detail": "Invalid username or password"})


@app.exception_handler(InvalidToken)
async def handle_invalid_token(request: Request, exc: InvalidToken):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid or expired token"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(InsufficientPermissions)
async def handle_insufficient_permissions(request: Request, exc: InsufficientPermissions):
    return JSONResponse(status_code=403, content={"detail": "You don't have permission to do this"})


@app.exception_handler(UserNotFound)
async def handle_user_not_found(request: Request, exc: UserNotFound):
    return JSONResponse(status_code=404, content={"detail": "User not found"})


@app.exception_handler(UsernameAlreadyExists)
async def handle_username_exists(request: Request, exc: UsernameAlreadyExists):
    return JSONResponse(status_code=400, content={"detail": "Username already taken"})


@app.exception_handler(EmailAlreadyExists)
async def handle_email_exists(request: Request, exc: EmailAlreadyExists):
    return JSONResponse(status_code=400, content={"detail": "Email address already registered"})


@app.exception_handler(InvalidResetToken)
async def handle_invalid_reset_token(request: Request, exc: InvalidResetToken):
    return JSONResponse(status_code=400, content={"detail": "Invalid or expired reset token"})


@app.exception_handler(CannotSelfModify)
async def handle_cannot_self_modify(request: Request, exc: CannotSelfModify):
    return JSONResponse(status_code=403, content={"detail": "You cannot delete or demote your own admin account"})


@app.exception_handler(LastAdminProtected)
async def handle_last_admin_protected(request: Request, exc: LastAdminProtected):
    return JSONResponse(status_code=409, content={"detail": "Cannot remove or demote the last admin account"})


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(books.router)
app.include_router(borrowings.router)
app.include_router(admin.router)
app.include_router(analytics.router)
app.include_router(reports.router)