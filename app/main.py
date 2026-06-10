from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import database, models
from app.database import engine
from app.routers import books, borrowings, admin, auth, users 
from app.exceptions import (
    BookNotFound,
    BookNotAvailable,
    BorrowingNotFound,
    BorrowLimitExceeded,
    DuplicateActiveBorrowing,
    InvalidCredentials,
    InvalidToken,
    InsufficientPermissions,
    UserNotFound,
    UsernameAlreadyExists,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    yield


app = FastAPI(title="Library Book Borrowing System", lifespan=lifespan)


# Existing handlers...
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


app.include_router(auth.router)  
app.include_router(users.router)        
app.include_router(books.router)
app.include_router(borrowings.router)
app.include_router(admin.router)