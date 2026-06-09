from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import database
import models  # noqa: F401
from database import engine
from router import books, borrowings, admin 
from exceptions import BookNotFound, BookNotAvailable, BorrowingNotFound, BorrowLimitExceeded,DuplicateActiveBorrowing


@asynccontextmanager
async def lifespan(app: FastAPI):
    # async with engine.begin() as conn:
    #     await conn.run_sync(database.Base.metadata.create_all)
    yield


app = FastAPI(title="Library Book Borrowing System", lifespan=lifespan)


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
    return JSONResponse(
        status_code=400,
        content={"detail": "User has reached the maximum of 3 active borrowings"}
    )


@app.exception_handler(DuplicateActiveBorrowing)
async def handle_duplicate_borrow(request: Request, exc: DuplicateActiveBorrowing):
    return JSONResponse(
        status_code=400,
        content={"detail": "User has already borrowed this book and not returned it"}
    )



app.include_router(books.router)
app.include_router(borrowings.router)
app.include_router(admin.router)